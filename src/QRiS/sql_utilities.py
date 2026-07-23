import re


def validate_sql_identifier(name: str) -> str:
    """
    Validate that a string is a safe SQL identifier (table or column name).
    Only allows letters, numbers, and underscores, and must start with a letter or underscore.
    Raises ValueError if invalid.
    """
    if not isinstance(name, str) or not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name):
        raise ValueError(f"Invalid SQL identifier: {name}")
    return name
