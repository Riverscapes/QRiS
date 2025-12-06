import os
from urllib.parse import urlparse
from pathlib import Path, PurePosixPath


def parse_posix_path(path: str) -> str:
    """This method returns a posix path no matter if you pass it a windows or a linux path

    Args:
        path ([type]): [description]
    """
    new_path = PurePosixPath(path.replace('\\', '/'))
    return str(new_path)


def safe_make_relpath(in_path: str, cwd_path: str) -> str:
    """ Safely create a relative path from an absolute path.
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
    """ Safely create an absolute path from a relative path

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
