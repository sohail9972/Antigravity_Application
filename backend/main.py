from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends, status
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
import git
import os
import shutil
import uuid
import asyncio
import datetime
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv
from typing import Optional, Dict, List, Any
from sqlmodel import Session, select, create_engine
from database import User, Task, engine, create_db_and_tables
from agent import repair_and_test_loop

load_dotenv()

# App Configuration
SECRET_KEY = os.getenv("JWT_SECRET", "antigravity-top-secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

app = FastAPI(title="Antigravity AI Backend")

# Initialize DB on startup
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- AUTH UTILITIES ---
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None: raise HTTPException(status_code=401, detail="Invalid credentials")
        with Session(engine) as session:
            user = session.get(User, user_id)
            if user is None: raise HTTPException(status_code=401, detail="User not found")
            return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Session expired")

# --- AUTH ENDPOINTS ---
class UserCreate(BaseModel):
    username: str
    password: str

@app.post("/api/auth/register")
async def register(req: UserCreate):
    with Session(engine) as session:
        existing = session.exec(select(User).where(User.username == req.username)).first()
        if existing: raise HTTPException(status_code=400, detail="Username already exists")
        hashed = pwd_context.hash(req.password)
        user = User(username=req.username, hashed_password=hashed)
        session.add(user)
        session.commit()
    return {"message": "Registration successful"}

@app.post("/api/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    with Session(engine) as session:
        user = session.exec(select(User).where(User.username == form_data.username)).first()
        if not user or not pwd_context.verify(form_data.password, user.hashed_password):
            raise HTTPException(status_code= status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
        
        token = create_access_token(data={"sub": str(user.id)})
        return {"access_token": token, "token_type": "bearer", "user": {"id": user.id, "username": user.username}}

@app.get("/api/auth/me")
async def get_me(user: User = Depends(get_current_user)):
    return {"id": user.id, "username": user.username}

# --- REPO ANALYSIS LOGIC ---
class AnalyzeRequest(BaseModel):
    repo_url: str

task_queues: Dict[str, asyncio.Queue] = {}

async def process_repo(repo_url: str, task_id: str, user_id: int):
    queue: Optional[asyncio.Queue] = task_queues.get(task_id)
    if queue is None: return

    try:
        # Move repos out of backend to avoid uvicorn reloading on every file change
        base_repos_dir = os.path.join(os.path.dirname(os.getcwd()), "repos")
        repo_dir = os.path.join(base_repos_dir, task_id)
        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)
        os.makedirs(base_repos_dir, exist_ok=True)
        
        await queue.put(f"🌐 Target Repository: {repo_url}\\n")
        await queue.put(f"📂 Workspace: {repo_dir}\\n")
        await queue.put("📥 Cloning repository...\\n")
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, git.Repo.clone_from, repo_url, repo_dir)
        
        await queue.put("✅ Clone complete. Initializing analysis...\\n")

        # Smart file selection: find the largest Python file that isn't a test or setup file
        potential_files = []
        for root, dirs, files in os.walk(repo_dir):
            if any(d in root for d in [".git", "vode_modules", ".pytest_cache", "__pycache__", "tests"]):
                continue
            for file in files:
                if file.endswith(".py") and not file.startswith("test_") and file != "setup.py":
                    full_path = os.path.join(root, file)
                    potential_files.append((full_path, os.path.getsize(full_path)))

        if not potential_files:
            await queue.put("❌ No suitable Python source files found for analysis.\\n")
            return

        potential_files.sort(key=lambda x: x[1], reverse=True)
        target_python_file = potential_files[0][0]

        await queue.put(f"🔍 Selected target for testing: {os.path.relpath(target_python_file, repo_dir)}\\n")
        
        with open(target_python_file, "r", encoding="utf-8") as f:
            source_code = f.read()

        import json # To handle report parsing
        final_report = None
        agent_generator = repair_and_test_loop(source_code, target_python_file)
        
        for log_msg in agent_generator:
            await queue.put(log_msg)
            if log_msg.startswith("[REPORT]"):
                final_report = json.loads(log_msg[8:])
            await asyncio.sleep(0.1)
        
        # Save results to DB
        with Session(engine) as session:
            task = session.exec(select(Task).where(Task.task_id == task_id)).first()
            if task and final_report:
                task.status = "completed" if final_report.get("success") else "failed"
                task.coverage = str(final_report.get("coverage", "0%"))
                task.test_code = str(final_report.get("test_code", ""))
                session.add(task)
                session.commit()

        await queue.put("\\n✨ **Full analysis cycle completed.**\\n")
    except Exception as e:
        await queue.put(f"❌ Critical System Error: {str(e)}\\n")
    finally:
        await queue.put("[DONE]")

@app.post("/api/analyze")
async def analyze_repo(req: AnalyzeRequest, background_tasks: BackgroundTasks, user: User = Depends(get_current_user)):
    task_id = str(uuid.uuid4())
    task_queues[task_id] = asyncio.Queue()
    
    with Session(engine) as session:
        new_task = Task(task_id=task_id, user_id=user.id, repo_url=req.repo_url)
        session.add(new_task)
        session.commit()
        
    background_tasks.add_task(process_repo, req.repo_url, task_id, user.id)
    return {"task_id": task_id}

@app.get("/api/stream/{task_id}")
async def stream_logs(task_id: str):
    if task_id not in task_queues:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
    queue = task_queues[task_id]

    async def event_generator():
        while True:
            msg = await queue.get()
            if msg == "[DONE]":
                yield f"data: [DONE]\\n\\n"
                task_queues.pop(task_id, None)
                break
            formatted_msg = msg.replace("\\n", "<br>")
            yield f"data: {formatted_msg}\\n\\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# --- DATA MANAGEMENT ENDPOINTS ---

@app.get("/api/tasks")
async def get_tasks(user: User = Depends(get_current_user)):
    with Session(engine) as session:
        tasks = session.exec(select(Task).where(Task.user_id == user.id).order_by(Task.created_at.desc())).all()
    return tasks

@app.get("/api/tasks/{task_id}")
async def get_task_details(task_id: str, user: User = Depends(get_current_user)):
    with Session(engine) as session:
        task = session.exec(select(Task).where(Task.task_id == task_id, Task.user_id == user.id)).first()
        if not task: raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str, user: User = Depends(get_current_user)):
    with Session(engine) as session:
        task = session.exec(select(Task).where(Task.task_id == task_id, Task.user_id == user.id)).first()
        if not task: raise HTTPException(status_code=404, detail="Task not found")
        session.delete(task)
        session.commit()
    return {"message": "Success"}
