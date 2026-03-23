# 🛰️ Antigravity AI — Autonomous Unit Test Case Generator

> *"Point it at any Python repo. It writes, runs, and fixes unit tests for you — automatically."*

---

## 📋 Table of Contents
- [Problem Statement](#problem-statement)
- [Our Solution](#our-solution)
- [Key Features](#key-features)
- [How It Works](#how-it-works)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Installation & Setup](#installation--setup)
- [API Reference](#api-reference)
- [Challenges & Learnings](#challenges--learnings)
- [Future Enhancements](#future-enhancements)
- [Team Members](#team-members)
- [License](#license)

---

## 🔴 Problem Statement

Writing unit tests is one of the most critical yet time-consuming tasks in software development. Developers often skip it due to time pressure, unfamiliarity, or the complexity of the codebase. This leads to:

- **Low code coverage**, hiding bugs until they reach production.
- **Slow development cycles**, with manual QA taking up enormous time.
- **Technical debt** that compounds as projects scale.

There was no tool that could look at an arbitrary Python codebase and *automatically produce a passing, high-coverage unit test suite* — until now.

---

## ✅ Our Solution

**Antigravity AI** is a full-stack web application that takes a **GitHub repository URL** as input and uses **Google Gemini 1.5 Flash** to autonomously:

1. Clone the repository.
2. Identify the most logic-rich Python file.
3. Generate a complete unit test file.
4. Execute the tests and capture failures.
5. Repair broken tests using AI reasoning on the failure logs.
6. Repeat until all tests pass.
7. Save the final test suite and code coverage to the user's dashboard.

**No manual coding. No test writing. Just a GitHub link.**

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🤖 **AI Test Generation** | Gemini 1.5 Flash reads source code and writes contextually accurate unit tests |
| 🔁 **Self-Healing Loop** | If tests fail, the AI reads the error output and auto-repairs them (up to 5 cycles) |
| 📊 **Coverage Tracking** | Real-time code coverage % extracted using `pytest-cov` |
| 💎 **Premium Live UI** | Glassmorphism design with real-time log streaming via Server-Sent Events |
| 🔐 **User Authentication** | Secure multi-user system with JWT sessions and bcrypt-hashed passwords |
| 🗂️ **Private Workspaces** | Each user has an isolated dashboard of all their past test generation runs |
| 📜 **History & Reports** | Every generated test suite is persistently stored for review and download |

---

## ⚙️ How It Works

```
GitHub URL Input
       │
       ▼
  1. Clone Repository (GitPython)
       │
       ▼
  2. Scan & Select Best Python File
       (largest non-test source file)
       │
       ▼
  3. Gemini AI Analyzes Source Code
       → Generates Full Unit Test File
       │
       ▼
  4. Execute Tests (Pytest + Coverage)
       │
     Pass? ──── YES ──────────────────────────┐
       │                                       │
      NO                                       │
       │                                       │
  5. AI Reads Failure Logs & Repairs Tests     │
       │                                       │
  6. Loop (max 5 iterations)                  │
       │                                       │
       └──────────────────────────────────────┘
       │
       ▼
  7. Final Report Generated
      → Coverage % + Test Code Saved to DB
      → Displayed in User Dashboard
```

---

## 🛠️ Tech Stack

### Backend
| Technology | Role |
|---|---|
| **FastAPI** | High-performance REST API & Server-Sent Events |
| **Google Gemini 1.5 Flash** | Core AI for test generation and self-repair |
| **SQLModel + SQLite** | ORM-based persistent storage for users and tasks |
| **Pytest + pytest-cov** | Test execution engine & coverage measurement |
| **python-jose + passlib** | JWT authentication & bcrypt password hashing |
| **GitPython** | Programmatic GitHub repository cloning |
| **python-dotenv** | Secure environment variable management |

### Frontend
| Technology | Role |
|---|---|
| **React.js (Vite)** | Modern reactive UI framework |
| **Vanilla CSS** | Custom glassmorphism design system |
| **Server-Sent Events (SSE)** | Real-time log streaming from agent to browser |
| **localStorage** | Persistent JWT session management |

---

## 🏗️ Architecture

```
┌─────────────────────┐         ┌────────────────────────┐
│    React Frontend   │ ←─SSE─→ │   FastAPI Backend      │
│                     │         │                        │
│  • Auth (Sign In/Up)│ ←─────→ │  • JWT Auth            │
│  • Repo URL Input   │         │  • SQLite DB           │
│  • Live Terminal    │         │  • Task Queue (async)  │
│  • History View     │         │  • Git Cloning         │
└─────────────────────┘         └──────────┬─────────────┘
                                            │
                                            ▼
                                 ┌──────────────────────┐
                                 │   AI Agent (agent.py)│
                                 │                      │
                                 │  • Gemini API Calls  │
                                 │  • Pytest Execution  │
                                 │  • Repair Loop       │
                                 └──────────────────────┘
```

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.10+
- Node.js & npm
- Git
- A free Google Gemini API key → [Get one here](https://aistudio.google.com/)

### Step 1 — Clone
```bash
git clone https://github.com/sohail9972/Antigravity_Application.git
cd Antigravity_Application
```

### Step 2 — Backend Setup
```bash
cd backend
pip install -r requirements.txt
```

### Step 3 — Frontend Setup
```bash
cd ../frontend
npm install
```

### Step 4 — Configure Environment
Create `backend/.env` with:
```env
GOOGLE_API_KEY=your_gemini_api_key_here
JWT_SECRET=any_random_secret_string
```

### Step 5 — Launch
```bash
# Run from the root project directory
python start_app.py
```

Open: **http://localhost:5173**

---

## 📡 API Reference

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/auth/register` | ❌ | Register a new user |
| `POST` | `/api/auth/login` | ❌ | Login and receive JWT token |
| `GET` | `/api/auth/me` | ✅ | Get current authenticated user |
| `POST` | `/api/analyze` | ✅ | Trigger test generation for a repo |
| `GET` | `/api/stream/{task_id}` | ❌ | Stream live AI agent logs (SSE) |
| `GET` | `/api/tasks` | ✅ | View all past analysis sessions |
| `GET` | `/api/tasks/{task_id}` | ✅ | Get full details of a specific run |
| `DELETE` | `/api/tasks/{task_id}` | ✅ | Remove a task from history |

---

## 🧠 Challenges & Learnings

- **Server Reloads Killing Sessions**: Uvicorn's `--reload` mode was restarting the server every time a new repo was cloned (since the files landed inside the `backend/` folder). Fixed by moving the workspace directory **outside** the watched directory.
- **Gemini JSON Mode**: Prompted the model with `response_mime_type: "application/json"` for structured, reliable output. Built a fallback JSON extractor for edge cases.
- **Multi-user Isolation**: Linking every analysis task to a specific user ID in the database ensures full workspace isolation between accounts.
- **Real-time Streaming**: Used FastAPI's `StreamingResponse` with `text/event-stream` to push live log messages to the browser without polling.

---

## 🚀 Future Enhancements

- [ ] **File Browser**: Let the user manually select which file in the repo to test, instead of auto-selection.
- [ ] **Multi-language Support**: Extend beyond Python to support JavaScript, Java, and Go.
- [ ] **GitHub OAuth**: One-click login via GitHub account for seamless repo access.
- [ ] **PR Integration**: Automatically open a Pull Request in the target repository with the generated test file.
- [ ] **Export Reports**: Download the full analysis report as a Markdown or PDF document.
- [ ] **Test Quality Scoring**: Use a secondary AI pass to assess test quality beyond just pass/fail.

---

## 👨‍💻 Team Members

| Name | Role |
|---|---|
| **Sohail** | Full-Stack Developer & AI Integration Lead |

---

## 🙏 Acknowledgments

- **Google AI (Gemini 1.5 Flash)** for the powerful and affordable AI backbone.
- **FastAPI** for making async Python backends a joy to build.
- **Hack2Skill** for organizing a hackathon that encourages real-world, impactful AI solutions.

---

## 📄 License

This project is licensed under the **MIT License**.

---

## 📌 Project Status

🟢 **Active** — Core features complete. Submitted for Hack2Skill 2026.
