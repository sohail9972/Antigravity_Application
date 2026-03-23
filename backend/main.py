from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import git
import os
import shutil
import uuid
import asyncio
from agent import repair_and_test_loop

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    repo_url: str

# In-memory queues to push log messages to streaming clients
from typing import Dict, Optional
task_queues: Dict[str, asyncio.Queue] = {}

async def process_repo(repo_url: str, task_id: str):
    queue: Optional[asyncio.Queue] = task_queues.get(task_id)
    if queue is None:
        return
        
    # for the type checker
    assert queue is not None

    try:
        repo_dir = f"repos/{task_id}"
        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)
        os.makedirs("repos", exist_ok=True)
        
        await queue.put(f"🚀 Cloning repository: {repo_url}\\n")
        
        # Run synchronous git clone in a threadpool so it doesn't block the async event loop
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, git.Repo.clone_from, repo_url, repo_dir)
        
        await queue.put(f"✅ Repository cloned successfully.\\n")

        await queue.put("🔍 Analyzing repository files...\\n")
        target_python_file = None
        for root, dirs, files in os.walk(repo_dir):
            for file in files:
                if file.endswith(".py") and not file.startswith("test_"):
                    target_python_file = os.path.join(root, file)
                    break
            if target_python_file:
                break

        if not target_python_file:
            await queue.put("❌ No Python source files found. Terminating.\\n")
            await queue.put("[DONE]")
            return

        await queue.put(f"🎯 Found target file: {os.path.basename(target_python_file)}\\n")
        
        with open(target_python_file, "r", encoding="utf-8") as f:
            source_code = f.read()

        agent_generator = repair_and_test_loop(source_code, target_python_file)
        for log_msg in agent_generator:
            await queue.put(log_msg)
            await asyncio.sleep(0.5)
        
        await queue.put("\\n✨ Analysis complete!\\n")
    except Exception as e:
        await queue.put(f"❌ Error processing repo: {str(e)}\\n")
    finally:
        await queue.put("[DONE]")

@app.post("/api/analyze")
async def analyze_repo(req: AnalyzeRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    task_queues[task_id] = asyncio.Queue()
    background_tasks.add_task(process_repo, req.repo_url, task_id)
    return {"task_id": task_id}

@app.get("/api/stream/{task_id}")
async def stream_logs(task_id: str):
    if task_id not in task_queues:
        raise HTTPException(status_code=404, detail="Task ID not found")
        
    queue = task_queues[task_id]

    async def event_generator():
        while True:
            msg = await queue.get()
            if msg == "[DONE]":
                yield f"data: [DONE]\\n\\n"
                break
            # Replace physical newlines with encoded newlines if necessary, 
            # though SSE expects data to just be string content.
            # Using basic data block format for SSE:
            formatted_msg = msg.replace("\\n", "<br>")
            yield f"data: {formatted_msg}\\n\\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
