import re
import requests
import importlib.util
import os
import glob

# Patterns to match add_standard_form_buttons and add_help_button usage
PATTERNS = [
    re.compile(r"add_standard_form_buttons\([^,]+,\s*['\"]([^'\"]+)['\"]"),
    re.compile(r"add_help_button\([^,]+,\s*['\"]([^'\"]+)['\"]")
]

# Base URL for help docs (adjust if needed)
BASE_URL = "https://qris.riverscapes.net/"

# Find all .py files in src/view
view_dir = os.path.join(os.path.dirname(__file__), '../src/view')
py_files = glob.glob(os.path.join(view_dir, '**', '*.py'), recursive=True)



def extract_help_slugs(file_path):
    slugs = set()
    with open(file_path, encoding='utf-8') as f:
        for line in f:
            for pat in PATTERNS:
                for match in pat.finditer(line):
                    slugs.add((file_path, match.group(1)))
    return slugs

def test_help_links():
    all_slug_tuples = set()
    for py_file in py_files:
        all_slug_tuples.update(extract_help_slugs(py_file))
    assert all_slug_tuples, "No help slugs found in forms."
    errors = []
    for file_path, slug in all_slug_tuples:
        url = BASE_URL + "/software-help/" + slug.lstrip('/')
        try:
            resp = requests.get(url)
            if resp.status_code != 200:
                errors.append(f"Invalid help URL in {os.path.basename(file_path)}: {url} (status {resp.status_code})")
        except Exception as ex:
            errors.append(f"Error accessing help URL in {os.path.basename(file_path)}: {url} ({ex})")
    if errors:
        for err in errors:
            print(err)
        raise AssertionError(f"{len(errors)} invalid help URLs found.")

if __name__ == "__main__":
    test_help_links()
    print("All help links are valid!")
