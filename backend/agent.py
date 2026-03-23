import json
import subprocess
import os
import sys
from typing import Optional
import google.generativeai as genai
from dotenv import load_dotenv

# Load key from .env file
load_dotenv()

# Initialize Gemini client using updated env var
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

def call_llm(prompt: str) -> str:
    """
    Real Gemini model call with mock fallback
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return _mock_llm_response(prompt)
    
    try:
        # Using gemini-1.5-flash for speed and JSON reliability
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        # Requesting JSON output specifically
        response = model.generate_content(
            f"SYSTEM ROLE: You are an expert software developer and tester. Always respond in valid JSON format.\n\nUSER PROMPT: {prompt}",
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json"
            )
        )
        return response.text
    except Exception as e:
        return json.dumps({"error": f"Gemini Error: {str(e)}", "action": "stop"})

def _mock_llm_response(prompt: str):
    # Simulated multi-step repair behavior for local testing
    if "math_utils" in prompt and "test_results" not in prompt:
         return json.dumps({
            "analysis": "Gemini Simulation: Analyzing code structure and generating initial tests.",
            "action": "generate",
            "test_code": "import math_utils\n\ndef test_add():\n    assert math_utils.add(2, 2) == 4\n\ndef test_divide():\n    assert math_utils.divide(10, 2) == 5.0\n",
            "fixes_applied": "Initial generation",
            "failure_type": "none",
            "confidence": "high"
        })
    else:
        return json.dumps({
            "analysis": "Gemini Simulation: Fixing tests based on recent execution results.",
            "action": "fix",
            "test_code": "import math_utils\nimport pytest\n\ndef test_add():\n    assert math_utils.add(2, 2) == 4\n\ndef test_divide():\n    assert math_utils.divide(10, 2) == 5.0\n\ndef test_divide_by_zero():\n    with pytest.raises(ValueError):\n        math_utils.divide(10, 0)\n",
            "fixes_applied": "Added division-by-zero edge case.",
            "failure_type": "none",
            "confidence": "high"
        })

def safe_parse_llm_json(text: str):
    try:
        text = text.strip()
        # Clean up possible markdown artifacts if JSON mode was ignored
        if "```" in text:
            parts = text.split("```")
            for part in parts:
                if "{" in part and "}" in part:
                    text = part
                    if text.startswith("json"): text = text[4:].strip()
                    break
        
        start_idx = text.find("{")
        end_idx = text.rfind("}")
        if start_idx == -1 or end_idx == -1: return None
        
        json_str = text[start_idx : end_idx + 1]
        return json.loads(json_str)
    except Exception:
        return None

def run_tests(framework: str, test_file_path: str) -> tuple[int, str, str]:
    test_dir = os.path.dirname(os.path.abspath(test_file_path)) or "."
    
    if framework == "pytest":
        command = [sys.executable, "-m", "pytest", "-q", "--cov=.", "--cov-report=term-missing", test_file_path]
    else:
        command = [sys.executable, test_file_path]

    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = test_dir
        result = subprocess.run(command, capture_output=True, text=True, timeout=30, cwd=test_dir, env=env)
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
    Goal: Generate and fix unit tests until they pass and cover the provided source code.
    
    Rules:
    - Do NOT modify source code.
    - Return FULL test file in 'test_code' field.
    - Analyze test failures/logs and fix them if they are test-related.
    - Stop if tests pass and coverage is sufficient.
    
    Input Context:
    {json.dumps(input_data, indent=2)}
    
    Return JSON response with schema:
    {{
      "analysis": "string explanation",
      "action": "generate" | "fix" | "stop",
      "test_code": "string",
      "fixes_applied": "string summary",
      "failure_type": "none" | "syntax" | "assertion" | "logic",
      "confidence": "high" | "medium" | "low"
    }}
    """

def repair_and_test_loop(source_code: str, source_file: str, framework: str = "pytest", max_iterations: int = 5):
    iteration = 1
    existing_tests = ""
    test_results = ""
    directory = os.path.dirname(os.path.abspath(source_file))
    basename = os.path.basename(source_file)
    test_file_path = os.path.join(directory, f"test_{basename}")

    yield f"🚀 Monitoring file: {os.path.basename(source_file)}\\n"

    while iteration <= max_iterations:
        yield f"\\n--- Iteration {iteration}/{max_iterations} [GEMINI] ---\\n"
        prompt = generate_prompt(source_code, existing_tests, test_results, framework, iteration, max_iterations)
        
        yield "🧠 Gemini is reasoning about code paths...\\n"
        llm_response_text = call_llm(prompt)
        
        response_data = safe_parse_llm_json(llm_response_text)
        if not response_data:
            yield "❌ LLM Integration Error: Invalid JSON Format detected.\\n"
            iteration += 1
            continue

        action = response_data.get("action", "stop")
        test_code = response_data.get("test_code", "")
        analysis = response_data.get("analysis", "No analysis provided.")

        yield f"🤖 Agent Analysis: {analysis}\\n"
        if action == "stop": break
        if not test_code.strip():
            iteration += 1
            continue

        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write(test_code)
        
        existing_tests = test_code
        yield f"💾 Tests written to {os.path.basename(test_file_path)}\\n"
        
        yield "🧪 Executing test suite...\\n"
        returncode, stdout, stderr = run_tests(framework, test_file_path)

        if returncode == 0:
            yield "✅ All tests passed successfully!\\n"
            test_results = stdout + "\\n" + stderr
            break
        else:
            yield f"⚠️ Tests failed in iteration {iteration}. Gemini will attempt repair...\\n"
            test_results = f"STDOUT:\\n{stdout}\\nSTDERR:\\n{stderr}\\n"
        
        iteration += 1

    import re
    coverage_pct = "0%"
    if test_results:
        match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+%)", test_results) or re.search(r"(\d+)%\s*$", test_results, re.MULTILINE)
        if match: coverage_pct = match.group(1) if "%" in match.group(0) else f"{match.group(1)}%"

    report = {
        "coverage": coverage_pct,
        "test_code": existing_tests,
        "success": iteration <= max_iterations if returncode == 0 else False
    }
    yield f"[REPORT]{json.dumps(report)}\\n"

