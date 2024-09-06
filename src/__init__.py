import re
from qgis.core import QgsMessageLog, Qgis
from ..__version__ import __version__

WHEEL_VERSION_PATTERN = r'.*rsxml-(\d+\.\d+\.\d+)-.*'

# This is how we import the rsxml module. We do this because we want to bundle the rsxml whl with this package
try:
    import sys
    import os
    wheels_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'wheels'))
    # Find the wheel file
    wheel_file = [f for f in os.listdir(wheels_dir) if f.startswith('rsxml-') and f.endswith('.whl')][0]
    if not wheel_file:
        QgsMessageLog.logMessage(f'Error loading rsxml from wheel file: no wheel file found in {wheels_dir}', 'QRis', Qgis.Critical)
        raise Exception(f'rsxml wheel not found in {wheels_dir}.')
    wheel_path = os.path.join(wheels_dir, wheel_file)
    wheel_version = re.match(WHEEL_VERSION_PATTERN, wheel_file).group(1)

    QgsMessageLog.logMessage(f'Found rsxml wheel file from {wheel_file} at version {str(wheel_version)}', 'QRis', Qgis.Info)

    # Remove any existing rsxml module from sys.modules
    if 'rsxml' in sys.modules:
        QgsMessageLog.logMessage('Removing rsxml from sys.modules', 'QRis', Qgis.Info)
        del sys.modules['rsxml']

    if wheel_path not in sys.path:
        QgsMessageLog.logMessage(f'Adding {wheel_path} to sys.path', 'QRis', Qgis.Info)
        # We add the path to sys.path so that we can import the module
        sys.path.insert(0, wheel_path)

    import rsxml
    QgsMessageLog.logMessage(f'rsxml imported from wheel: {rsxml.__path__}', 'QRis', Qgis.Info)


except ImportError:
    QgsMessageLog.logMessage('Error importing rsxml from wheels', 'QRis', Qgis.Critical)
    raise Exception('Error importing rsxml from wheels')
