import json
import subprocess
import os
import sys

# Mock LLM state
_mock_state = {"call_count": 0}


def call_llm(prompt: str) -> str:
    """
    Simulated LLM response (2-step repair loop)
    """
    _mock_state["call_count"] += 1

    if _mock_state["call_count"] == 1:
        return json.dumps({
            "analysis": "Generating initial failing tests.",
            "action": "generate",
            "test_code": """import math_utils

def test_add():
    assert math_utils.add(2, 2) == 5

def test_divide():
    assert math_utils.divide(10, 2) == 5.0
""",
            "fixes_applied": "Initial generation",
            "failure_type": "none",
            "confidence": "high"
        })
    else:
        return json.dumps({
            "analysis": "Fixing incorrect assertion (2+2 != 5).",
            "action": "fix",
            "test_code": """import math_utils
import pytest

def test_add():
    assert math_utils.add(2, 2) == 4

def test_divide():
    assert math_utils.divide(10, 2) == 5.0

def test_divide_by_zero():
    with pytest.raises(ValueError):
        math_utils.divide(10, 0)
""",
            "fixes_applied": "Corrected assertion and added edge case",
            "failure_type": "assertion",
            "confidence": "high"
        })


def safe_parse_llm_json(text: str):
    """
    Robust JSON extraction from LLM response
    """
    try:
        text = text.strip()

        if "```" in text:
            parts = text.split("```")
            text = parts[1] if len(parts) > 1 else parts[0]

        start_idx = int(text.find("{"))
        end_idx = int(text.rfind("}"))

        if start_idx == -1 or end_idx == -1:
            raise ValueError("No JSON found")
            
        slice_end = end_idx + 1
        json_str: str = text[start_idx:slice_end]
        return json.loads(json_str)

    except Exception as e:
        print(f"❌ JSON parse error: {e}")
        return None


def run_tests(framework: str, test_file_path: str) -> tuple[int, str, str]:
    """
    Executes tests with proper environment handling
    """
    if framework == "pytest":
        command = [sys.executable, "-m", "pytest", "-q"]
    elif framework == "unittest":
        command = [sys.executable, "-m", "unittest", "discover"]
    elif framework == "jest":
        command = ["npx", "jest"]
    else:
        command = [sys.executable, test_file_path]

    try:
        test_dir = os.path.dirname(os.path.abspath(test_file_path)) or "."

        env = os.environ.copy()
        env["PYTHONPATH"] = test_dir  # 🔥 critical fix

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=test_dir,
            env=env
        )

        return result.returncode, result.stdout, result.stderr

    except subprocess.TimeoutExpired:
        return 1, "", "Test execution timed out."
    except Exception as e:
        return 1, "", str(e)


def generate_prompt(source_code, existing_tests, test_results, framework, iteration, max_iterations) -> str:
    """
    Constructs prompt for LLM
    """
    input_data = {
        "source_code": source_code,
        "existing_tests": existing_tests,
        "test_results": test_results,
        "framework": framework,
        "iteration": iteration,
        "max_iterations": max_iterations
    }

    return f"""
You are an autonomous Software Test Generation and Repair Agent.

Goal:
- Generate and fix unit tests until they pass.

Rules:
- Do NOT modify source code
- Return FULL test file
- Fix failures based on logs

Input:
{json.dumps(input_data, indent=2)}

Return ONLY JSON.
"""


def repair_and_test_loop(source_code: str, source_file: str, framework: str = "pytest", max_iterations: int = 5):
    iteration = 1
    existing_tests = ""
    test_results = ""

    directory = os.path.dirname(os.path.abspath(source_file))
    basename = os.path.basename(source_file)

    test_file_name = f"test_{basename}"
    test_file_path = os.path.join(directory, test_file_name)

    print(f"🚀 Starting loop for {source_file}")

    while iteration <= max_iterations:
        print(f"\n--- Iteration {iteration}/{max_iterations} ---")

        prompt = generate_prompt(
            source_code,
            existing_tests,
            test_results,
            framework,
            iteration,
            max_iterations
        )

        print("🤖 Calling LLM...")
        llm_response_text = call_llm(prompt)

        print("\n--- RAW LLM RESPONSE ---")
        print(llm_response_text)
        print("------------------------")

        response_data = safe_parse_llm_json(llm_response_text)

        if not response_data:
            iteration += 1
            continue

        action = response_data.get("action", "stop")
        test_code = response_data.get("test_code", "")

        print(f"Action: {action}")

        if action == "stop":
            break

        if not test_code.strip():
            print("⚠️ Empty test code. Skipping...")
            iteration += 1
            continue

        with open(test_file_path, "w") as f:
            f.write(test_code)

        existing_tests = test_code
        print(f"💾 Test saved: {test_file_path}")

        print("🧪 Running tests...")
        returncode, stdout, stderr = run_tests(framework, test_file_path)

        if returncode == 0:
            print("✅ All tests passed!")
            break
        else:
            print("❌ Tests failed")

            test_results = f"""
TEST EXECUTION RESULT:
Exit Code: {returncode}

STDOUT:
{stdout}

STDERR:
{stderr}
"""

        iteration += 1

    if iteration > max_iterations:
        print("⚠️ Max iterations reached")
    else:
        print("🎉 Finished successfully!")


if __name__ == "__main__":
    dummy_source = '''
def add(a, b):
    return a + b

def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
'''

    with open("math_utils.py", "w") as f:
        f.write(dummy_source)

    repair_and_test_loop(
        source_code=dummy_source,
        source_file="math_utils.py",
        framework="pytest",
        max_iterations=3
    )