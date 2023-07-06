from ..__version__ import __version__

RSXML_VERSION = '2.0.1'

# This is how we import the rsxml module. We do this because we want to bundle the rsxml whl with this package
try:
    import rsxml
    print('rsxml imported from site-packages')
except ImportError:
    import sys
    import os
    this_dir = os.path.dirname(os.path.realpath(__file__))
    path = os.path.join(this_dir, '..', 'wheels', f'rsxml-{RSXML_VERSION}-py3-none-any.whl')
    sys.path.append(path)
    if not os.path.exists(path):
        raise Exception('rsxml wheel not found at {}.'.format(path))
    import rsxml
    print('rsxml imported from wheels')
