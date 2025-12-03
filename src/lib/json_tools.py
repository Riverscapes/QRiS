import json

def json_repair(s):
    # Try to close open curly braces and quotes
    s = s.strip()
    # If string ends with an open quote, close it
    if s.count('"') % 2 != 0:
        s += '"'
    # If string ends with an open curly brace, close it
    if s.count('{') > s.count('}'):
        s += '}' * (s.count('{') - s.count('}'))
    # If string ends with an open square bracket, close it
    if s.count('[') > s.count(']'):
        s += ']' * (s.count('[') - s.count(']'))
    try:
        return json.loads(s)
    except Exception as e:
        print(f"Best effort repair failed: {e} | {s[:100]}...")
        return {}

# Usage:
# meta = json_repair(value)

def safe_json_loads(s: str):
    try:
        return json.loads(s)
    except json.JSONDecodeError as e:
        # Log the error and attempt to repair
        print(f"JSON decode error: {e} | Attempting to repair...")
        repaired = json_repair(s)
        if repaired is not None:
            return repaired
        return None  # or handle as appropriate