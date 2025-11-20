try:
    # When src is a subpackage of QRiS
    from ..__version__ import __version__  # type: ignore
except ImportError:
    # When running src as top-level package
    from __version__ import __version__  # type: ignore
