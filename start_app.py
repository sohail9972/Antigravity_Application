import subprocess
import time
import os
import sys

def start_backend():
    print("🚀 Starting FastAPI Backend...")
    return subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--port", "8001"],
        cwd=os.path.join(os.getcwd(), "backend")
    )

def start_frontend():
    print("🌐 Starting Vite Frontend...")
    # Using npx vite to ensure it runs correctly across environments
    return subprocess.Popen(
        ["npx", "vite"],
        cwd=os.path.join(os.getcwd(), "frontend"),
        shell=True
    )

if __name__ == "__main__":
    if not os.environ.get("GOOGLE_API_KEY"):
        print("⚠️  Warning: GOOGLE_API_KEY not found in environment.")
        print("💡 The agent will run in [GEMINI MOCK] mode. Set the key to enable real AI features.")
        print("-" * 50)

    try:
        backend_proc = start_backend()
        time.sleep(2)  # Give backend a moment to bind to port
        frontend_proc = start_frontend()

        print("\n" + "=" * 50)
        print("✅ Antigravity Application is Ready!")
        print("Backend: http://localhost:8001")
        print("Frontend: http://localhost:5173")
        print("=" * 50)
        print("\nPress Ctrl+C to terminate both servers.")

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping servers...")
        backend_proc.terminate()
        frontend_proc.terminate()
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error occurred: {e}")
        if 'backend_proc' in locals(): backend_proc.terminate()
        if 'frontend_proc' in locals(): frontend_proc.terminate()
