# Antigravity AI 🛰️

## Autonomous Test Generation & Repair Agent

**Antigravity AI** is a state-of-the-art autonomous testing agent designed to take any Python repository and automatically generate, verify, and repair unit tests. Powered by **Google Gemini 1.5 Flash**, it uses a self-healing loop to analyze test failures and iteratively fix them until they pass and achieve high code coverage.

![Project Preview](https://github.com/sohail9972/Antigravity_Application/blob/main/frontend/screenshot.png) *(Placeholder if you add a screenshot)*

---

## ✨ Features

- 🧠 **Autonomous Repair Loop**: Real-time reasoning to generate, execute, and fix unit tests automatically.
- 💎 **Premium Glassmorphism UI**: High-aesthetic modern design with live-scrolling logs and a status timeline.
- 🔐 **Multi-user Authentication**: Secure Sign-in and Sign-up functionality with JWT and bcrypt-hashed passwords.
- 📜 **Historical Analysis**: Every test run is saved to a persistent SQLite database for later review.
- 🔍 **Intelligent File Selection**: Automatically scans repositories to find the most critical logic files for testing.
- 📊 **Coverage Tracking**: Real-time extraction of actual code coverage using `pytest-cov`.

---

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.10+)
- **AI Integration**: Google Generative AI (Gemini 1.5 Flash)
- **Database**: SQLModel with SQLite
- **Security**: JWT Authentication / Passlib
- **Testing**: Pytest & Pytest-Cov

### Frontend
- **Framework**: React.js (Vite)
- **Styling**: Vanilla CSS (Premium Glassmorphism Theme)
- **Utilities**: Lucide Icons (Optional/System Fonts)

---

## 🚀 Getting Started

### 📝 Prerequisites
- Python 3.10+
- Node.js & npm
- Git

### 🔧 Installation

1. **Clone the Repo**:
   ```bash
   git clone https://github.com/sohail9972/Antigravity_Application.git
   cd Antigravity_Application
   ```

2. **Backend Setup**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Frontend Setup**:
   ```bash
   cd ../frontend
   npm install
   ```

### 🗝️ Configuration
Create a `.env` file in the `backend/` directory and add your Google Gemini API key:
```env
GOOGLE_API_KEY=your_gemini_key_here
JWT_SECRET=your_secret_here
```

### 🏃 Running the Application
Use our all-in-one launch script from the root directory:
```bash
python start_app.py
```
Then navigate to: **http://localhost:5173**

---

## 📖 How it Works

1. **Input**: User pastes a GitHub repository URL.
2. **Clone**: The agent clones the repository into an isolated workspace.
3. **Analyze**: It identifies the primary logic file using a size-based heuristic.
4. **Reasoning**: Gemini 1.5 Flash analyzes the source code and generates a full test suite.
5. **Repair Loop**:
   - Executes tests using `pytest`.
   - If tests fail, the stderr and logs are sent back to the AI.
   - The AI identifies the failure root cause and fixes the test case.
   - Repeat (up to 5 iterations) until 100% pass rate is reached.
6. **Persistence**: Final results, coverage, and repair iteration logs are saved to your private dashboard.

---

## 👨‍💻 Author
**Sohail**
Built for Hack2Skill Hackathon 2026.

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
