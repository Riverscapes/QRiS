from pathlib import Path, PurePosixPath


def parse_posix_path(path: str) -> str:
    """This method returns a posix path no matter if you pass it a windows or a linux path

    Args:
        path ([type]): [description]
    """
    new_path = PurePosixPath(path.replace('\\', '/'))
    return str(new_path)


def safe_make_relpath(in_path: str, cwd_path: str) -> str:
    """ Safely create an absolute path from a relative path

    if this fails then just return the input

    Args:
        in_path (str): _description_
        cwd_path (str): _description_

    Returns:
        str: _description_
    """
    if in_path and len(in_path) > 0 and os.path.isabs(in_path):
        return os.path.relpath(in_path, cwd_path)
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
