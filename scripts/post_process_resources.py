"""Post-process resources.py after pyrcc compilation.

Replaces the hardcoded PyQt5/PyQt6 import with the version-independent
qgis.PyQt wrapper, and strips the unnecessary UTF-8 coding comment.
"""

import re
import sys

filepath = sys.argv[1] if len(sys.argv) > 1 else "src/resources.py"

with open(filepath) as f:
    content = f.read()

content = re.sub(r"from PyQt[56] import QtCore", "from qgis.PyQt import QtCore", content)
content = re.sub(r"^# -\*- coding: utf-8 -\*-\n+", "", content)

with open(filepath, "w") as f:
    f.write(content)
