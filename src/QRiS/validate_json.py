import re
import json


def validate_json_file(file_path, schema):
    with open(file_path, "r") as file:
        data = json.load(file)
    valid, error_message = validate_json(data, schema)
    if not valid:
        print(error_message)
    return valid, error_message

def validate_json(data, schema):
    if "required" in schema:
        for key in schema["required"]:
            if key not in data:
                return False, f"Missing required key {key}"
    
    if "properties" in schema:
        for key, value in schema["properties"].items():
            if key not in data:
                return False, f"Missing key {key}"
            if "type" in value and type(data[key]).__name__ != value["type"]:
                return False, f"Incorrect type for key {key}"
            if "enum" in value and data[key] not in value["enum"]:
                return False, f"Invalid value for key {key}"
            if "pattern" in value and not re.match(value["pattern"], data[key]):
                return False, f"Value for key {key} does not match pattern"
            if value["type"] == "object":
                valid, error_message = validate_json(data[key], value)
                if not valid:
                    return False, error_message
    return True, ""