import pytest
from agent import safe_parse_llm_json

def test_safe_parse_llm_json_valid():
    text = """```json
{
  "action": "stop"
}
```"""
    assert safe_parse_llm_json(text) == {"action": "stop"}

def test_safe_parse_llm_json_no_json():
    text = "Just some text without JSON"
    assert safe_parse_llm_json(text) is None

def test_safe_parse_llm_json_malformed():
    text = '{"action": "stop"'
    assert safe_parse_llm_json(text) is None
