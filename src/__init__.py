try:
    from .__version__ import __version__
except ImportError:
    # During tests, relative imports might fail if package structure is confused
    __version__ = "0.0.0dev"

