import sys
sys.path.insert(0, "backend")
from agent import repair_and_test_loop

print("Starting debug loop")
try:
    code = "def func(): return 1"
    for msg in repair_and_test_loop(code, "repos/test/aws_lambda_handler.py"):
        print(msg)
except Exception as e:
    print(f"CRASH: {e}")
