# coding=utf-8
"""Common functionality used by regression tests."""

import sys
import os
import logging


LOGGER = logging.getLogger('QGIS')
QGIS_APP = None  # Static variable used to hold hand to running QGIS app
CANVAS = None
PARENT = None
IFACE = None


def get_qgis_app():
    """ Start one QGIS application to test against.

    :returns: Handle to QGIS app, canvas, iface and parent. If there are any
        errors the tuple members will be returned as None.
    :rtype: (QgsApplication, CANVAS, IFACE, PARENT)

    If QGIS is already running the handle to that app will be returned.
    """

    # We want to fail loudly if QGIS cannot be imported in tests
    from qgis.PyQt import QtGui, QtCore, QtWidgets
    from qgis.core import QgsApplication
    from qgis.gui import QgsMapCanvas
    try:
        from qgis_interface import QgisInterface
    except ImportError:
        from .qgis_interface import QgisInterface

    global QGIS_APP  # pylint: disable=W0603

    if QGIS_APP is None:
        # Suppress benign Qt mime database errors on Windows
        if 'QT_LOGGING_RULES' not in os.environ:
             os.environ['QT_LOGGING_RULES'] = 'qt.core.mimedb=false'
        
        # Check for and clear any mocks that might block real QGIS loading
        # This handles cases where test_analysis_*.py ran before us
        try:
            from unittest.mock import MagicMock
            if 'qgis' in sys.modules and isinstance(sys.modules['qgis'], MagicMock):
                LOGGER.debug("Detected mocked 'qgis' module. Clearing sys.modules to load real QGIS.")
                del sys.modules['qgis']
                # Remove all qgis submodules
                for mod in list(sys.modules.keys()):
                    if mod.startswith('qgis.'):
                        del sys.modules[mod]
        except ImportError:
            pass

        gui_flag = True  # All test will run qgis in gui mode
        #noinspection PyPep8Naming
        # QGIS_APP = QgsApplication(sys.argv, gui_flag)
        # Use dummy bytes args to avoid TypeError with Windows/SIP bindings
        QGIS_APP = QgsApplication([b"qgis_test"], gui_flag)
        # Make sure QGIS_PREFIX_PATH is set in your env if needed!
        if 'QGIS_PREFIX_PATH' in os.environ:
             QGIS_APP.setPrefixPath(os.environ['QGIS_PREFIX_PATH'], True)
        QGIS_APP.initQgis()
        s = QGIS_APP.showSettings()
        LOGGER.debug(s)

    global PARENT  # pylint: disable=W0603
    if PARENT is None:
        #noinspection PyPep8Naming
        PARENT = QtWidgets.QWidget()

    global CANVAS  # pylint: disable=W0603
    if CANVAS is None:
        #noinspection PyPep8Naming
        CANVAS = QgsMapCanvas(PARENT)
        CANVAS.resize(QtCore.QSize(400, 400))

    global IFACE  # pylint: disable=W0603
    if IFACE is None:
        # QgisInterface is a stub implementation of the QGIS plugin interface
        #noinspection PyPep8Naming
        IFACE = QgisInterface(CANVAS)

    return QGIS_APP, CANVAS, IFACE, PARENT
