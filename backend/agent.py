import json
import subprocess
import os
import sys

_mock_state = {"call_count": 0}

def call_llm(prompt: str) -> str:
    _mock_state["call_count"] += 1

    if _mock_state["call_count"] == 1:
        return json.dumps({
            "analysis": "Generating initial tests.",
            "action": "generate",
            "test_code": "import math_utils\n\ndef test_add():\n    assert math_utils.add(2, 2) == 4\n\ndef test_divide():\n    assert math_utils.divide(10, 2) == 5.0\n",
            "fixes_applied": "Initial generation",
            "failure_type": "none",
            "confidence": "high"
        })
    else:
        return json.dumps({
            "analysis": "Fixing tests.",
            "action": "fix",
            "test_code": "import math_utils\nimport pytest\n\ndef test_add():\n    assert math_utils.add(2, 2) == 4\n\ndef test_divide():\n    assert math_utils.divide(10, 2) == 5.0\n\ndef test_divide_by_zero():\n    with pytest.raises(ValueError):\n        math_utils.divide(10, 0)\n",
            "fixes_applied": "Corrected assertion and added edge case",
            "failure_type": "assertion",
            "confidence": "high"
        })

def safe_parse_llm_json(text: str):
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
        return None

def run_tests(framework: str, test_file_path: str) -> tuple[int, str, str]:
    if framework == "pytest":
        command = [sys.executable, "-m", "pytest", "-q", "--cov=.", "--cov-report=term-missing"]
    else:
        command = [sys.executable, test_file_path]

    try:
        test_dir = os.path.dirname(os.path.abspath(test_file_path)) or "."
        env = os.environ.copy()
        env["PYTHONPATH"] = test_dir

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

    yield f"🚀 Starting loop for {source_file}\\n"

    while iteration <= max_iterations:
        yield f"\\n--- Iteration {iteration}/{max_iterations} ---\\n"
        
        prompt = generate_prompt(source_code, existing_tests, test_results, framework, iteration, max_iterations)
        
        yield "🤖 Calling LLM...\\n"
        llm_response_text = call_llm(prompt)
        
        yield "\\n--- RAW LLM RESPONSE ---\\n"
        yield llm_response_text + "\\n"
        yield "------------------------\\n"

        response_data = safe_parse_llm_json(llm_response_text)

        if not response_data:
            yield "❌ Failed to parse JSON from LLM.\\n"
            iteration += 1
            continue

        action = response_data.get("action", "stop")
        test_code = response_data.get("test_code", "")

        yield f"Action: {action}\\n"

        if action == "stop":
            break

        if not test_code.strip():
            yield "⚠️ Empty test code. Skipping...\\n"
            iteration += 1
            continue

        with open(test_file_path, "w") as f:
            f.write(test_code)

        existing_tests = test_code
        yield f"💾 Test saved: {test_file_path}\\n"

        yield "🧪 Running tests...\\n"
        returncode, stdout, stderr = run_tests(framework, test_file_path)

        if returncode == 0:
            yield "✅ All tests passed!\\n"
            break
        else:
            yield "❌ Tests failed\\n"
            test_results = f"TEST EXECUTION RESULT:\\nExit Code: {returncode}\\nSTDOUT:\\n{stdout}\\nSTDERR:\\n{stderr}\\n"
            yield test_results

        iteration += 1

    import re
    coverage_pct = "0%"
    if test_results:
        match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+%)", test_results)
        if match:
            coverage_pct = match.group(1)

    final_test_code = existing_tests
    if os.path.exists(test_file_path):
        with open(test_file_path, "r", encoding="utf-8") as f:
            final_test_code = f.read()

    if iteration > max_iterations:
        yield "⚠️ Max iterations reached\\n"
    else:
        yield "🎉 Finished successfully!\\n"
        
    report = {
        "coverage": coverage_pct,
        "test_code": final_test_code,
        "success": iteration <= max_iterations
    }
    yield f"[REPORT]{json.dumps(report)}\\n"

