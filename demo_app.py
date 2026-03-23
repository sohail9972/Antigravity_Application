import threading
import uvicorn
import time
import requests
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))
from main import app

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")

server_thread = threading.Thread(target=run_server, daemon=True)
server_thread.start()

time.sleep(2)

repo_url = "https://github.com/sohail9972/CareGuide_AI.git"
print(f"Sending request to analyze {repo_url}...")
res = requests.post("http://127.0.0.1:8000/api/analyze", json={"repo_url": repo_url})
data = res.json()
task_id = data["task_id"]
print(f"Got Task ID: {task_id}\\n")

print("--- AGENT STREAM ---")
try:
    response = requests.get(f"http://127.0.0.1:8000/api/stream/{task_id}", stream=True)
    for line in response.iter_lines():
        if line:
            line = line.decode('utf-8')
            if line.startswith('data: '):
                print(line[6:].replace('<br>', ''))
except Exception as e:
    print(f"Stream ended or errored: {e}")
