import os
from pathlib import PurePosixPath
import subprocess
import sys
from urllib.parse import urlparse


def get_unique_file_path(folder: str, root_name: str, extension: str) -> str:
    """
    Generates a unique file path in the specified folder based on a root name and extension.
    If the file exists, it appends an incrementing number (e.g., _01, _02) to the filename.

    Args:
        folder (str): The directory where the file will be located.
        root_name (str): The base name for the file.
        extension (str): The file extension (without the dot, e.g., 'csv', 'xlsx').

    Returns:
        str: A full path to a file that is guaranteed not to exist (up to 99 iterations).
    """
    # Sanitize the root name: keep only alphanumeric characters, replace spaces with underscores
    # "remove spaces and punctuation" - interpreting as keeping alnum and maybe underscores if present?
    # User said "remove spaces and punctuation", usually implies keeping alnum.
    # Let's interpret "remove spaces" as replace with underscore or remove?
    # Example: "Jam Count Attributes" -> "jam_count_attributes" implies replacing spaces with underscores
    # and lowercasing.

    clean_name = root_name.lower().replace(" ", "_")
    clean_name = "".join([c for c in clean_name if c.isalnum() or c == "_"])

    # Ensure extension starts with dot if not present
    if not extension.startswith("."):
        extension = f".{extension}"

    candidate_name = f"{clean_name}{extension}"
    full_path = os.path.join(folder, candidate_name)

    if not os.path.exists(full_path):
        return full_path

    for i in range(100):
        candidate_name = f"{clean_name}_{i:02d}{extension}"
        full_path = os.path.join(folder, candidate_name)
        if not os.path.exists(full_path):
            return full_path

    return full_path


def parse_posix_path(path: str) -> str:
    """This method returns a posix path no matter if you pass it a windows or a linux path

    Args:
        path ([type]): [description]
    """
    new_path = PurePosixPath(path.replace("\\", "/"))
    return str(new_path)


def safe_make_relpath(in_path: str, cwd_path: str) -> str:
    """Safely create a relative path from an absolute path.
    If this fails (e.g., different drives), just return the input.
    """
    if in_path and len(in_path) > 0 and os.path.isabs(in_path):
        try:
            return os.path.relpath(in_path, cwd_path)
        except ValueError:
            # Different drives, can't make a relative path
            return in_path
    else:
        return in_path


def safe_make_abspath(in_path: str, cwd_path: str) -> str:
    """Safely create an absolute path from a relative path

    if this fails then just return the input

    Args:
        in_path (str): _description_
        cwd_path (str): _description_

    Returns:
        str: _description_
    """
    if in_path and len(in_path) > 0 and not os.path.isabs(in_path):
        return os.path.abspath(os.path.join(cwd_path, in_path))
    else:
        return in_path


def is_url(value):
    if not isinstance(value, str):
        return False
    # Optionally, check for empty string
    if not value:
        return False
    result = urlparse(value)
    return all([result.scheme, result.netloc])


def explore_folder(folder: str, create_if_missing: bool = False) -> None:
    """Generic method for opening finder or file explorer to a specific folder.

    Args:
        folder (str): The folder path to open.
        create_if_missing (bool, optional): Whether to create the folder if it doesn't exist. Defaults to False.
    """

    if not folder:
        return

    if create_if_missing and not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)

    if sys.platform == "darwin":
        subprocess.Popen(["open", folder])
    elif sys.platform == "win32":
        # Use os.startfile on Windows — it handles spaces and mixed slashes
        # without blocking, and doesn't depend on explorer.exe being in PATH.
        os.startfile(os.path.normpath(folder))
    else:
        subprocess.Popen(["xdg-open", folder])
