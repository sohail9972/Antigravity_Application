# 🛰️ Antigravity AI — Unit Test Case Generator

> **Automatically generate, execute, and repair unit tests for any Python GitHub repository using Google Gemini AI.**

Built for the **Hack2Skill Hackathon 2026**, Antigravity AI is a full-stack autonomous agent that takes a GitHub repository URL as input and produces a fully passing, high-coverage **unit test suite** — without any manual intervention.

---

## 🎯 What Does It Do?

Simply paste the URL of any Python GitHub repository and Antigravity AI will:

1. **Clone** the repository automatically.
2. **Scan & Select** the most important Python source file to test.
3. **Generate** a complete unit test file using Google Gemini 1.5 Flash.
4. **Execute** the tests and capture all pass/fail output.
5. **Repair** any failing tests intelligently by feeding results back into the AI.
6. **Repeat** the loop (up to 5 iterations) until all tests pass.
7. **Report** the final code coverage and generated tests in a beautiful UI.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🤖 **AI-Powered Generation** | Uses Google Gemini 1.5 Flash to reason about code and write accurate tests |
| 🔁 **Self-Healing Loop** | If tests fail, the AI reads the errors and repairs the tests automatically |
| 📊 **Coverage Reports** | Extracts real code coverage % using pytest-cov |
| 🔐 **User Authentication** | Secure Sign Up / Sign In with JWT tokens and bcrypt password hashing |
| 🗂️ **Personal Workspace** | Each user has an isolated history of all their past test generation sessions |
| 💎 **Premium UI** | Glassmorphism design with live log streaming and real-time status indicators |
| 📜 **Persistent History** | All generated test suites are stored in a database for later review |

---

## 🛠️ Tech Stack

### Backend
| Library | Purpose |
|---|---|
| **FastAPI** | High-performance REST API framework |
| **Google Generative AI** | Gemini 1.5 Flash for unit test generation & repair |
| **SQLModel + SQLite** | Lightweight database for users and task history |
| **Pytest + Pytest-Cov** | Test execution engine and coverage measurement |
| **PassLib + Python-Jose** | Secure password hashing and JWT session management |
| **GitPython** | Programmatic repository cloning |

### Frontend
| Library | Purpose |
|---|---|
| **React.js (Vite)** | Fast and reactive UI framework |
| **Vanilla CSS** | Custom glassmorphism design system |
| **Server-Sent Events** | Real-time log streaming from backend to browser |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js & npm
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/sohail9972/Antigravity_Application.git
cd Antigravity_Application
```

### 2. Install Backend Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 3. Install Frontend Dependencies
```bash
cd ../frontend
npm install
```

### 4. Configure Environment Variables
Create a `.env` file inside the `backend/` folder:
```env
GOOGLE_API_KEY=your_google_gemini_api_key
JWT_SECRET=any_secret_string_you_choose
```
> 🔑 Get your free Gemini API key from [Google AI Studio](https://aistudio.google.com/)

### 5. Launch the Application
From the **root** directory, run the all-in-one launcher:
```bash
python start_app.py
```
Then open your browser at: **http://localhost:5173**

---

## 🔄 How the Test Generation Loop Works

```
User Input (GitHub URL)
        │
        ▼
  Clone Repository
        │
        ▼
Scan & Select Target Python File
  (Largest non-test source file)
        │
        ▼
  Gemini Analyzes Source Code
  → Generates Unit Test File
        │
        ▼
   Pytest Runs Tests
        │
     ┌──┴──┐
   PASS    FAIL
     │       │
     │  Gemini Reads Error Logs
     │  → Repairs Failing Tests
     │       │
     │   Loop (max 5x)
     │       │
     └───────┘
        │
        ▼
  Final Report Saved
  (Coverage + Test Code)
```

---

## 📂 Project Structure

```
Antigravity_Application/
├── backend/
│   ├── agent.py           # 🤖 Core AI loop (generate & repair tests)
│   ├── main.py            # 🚀 FastAPI server, Auth & API endpoints
│   ├── database.py        # 🗄️  SQLite models (User, Task)
│   └── requirements.txt   # 📦 Python dependencies
├── frontend/
│   └── src/
│       ├── App.jsx        # ⚛️  Main React component (UI & routing)
│       └── index.css      # 💎 Premium glassmorphism styles
├── start_app.py           # ▶️  One-click launcher for both servers
├── .gitignore
└── README.md
```

---

## 📡 API Endpoints

| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| `POST` | `/api/auth/register` | ❌ | Create a new user account |
| `POST` | `/api/auth/login` | ❌ | Login and receive JWT token |
| `GET` | `/api/auth/me` | ✅ | Get current user details |
| `POST` | `/api/analyze` | ✅ | Start test generation for a repo |
| `GET` | `/api/stream/{task_id}` | ❌ | Stream live agent logs (SSE) |
| `GET` | `/api/tasks` | ✅ | List all your past test runs |
| `GET` | `/api/tasks/{task_id}` | ✅ | Get full details of a past run |
| `DELETE` | `/api/tasks/{task_id}` | ✅ | Delete a task from your history |

---

## 👨‍💻 Author

**Sohail** — Built for the Hack2Skill Hackathon 2026.

---

## 📄 License

This project is licensed under the **MIT License**.
