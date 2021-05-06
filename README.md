# Riverscapes Integrated Planning Tool (RIPT)


## Development resources

* [PyQGIS Developer Cookbook](https://docs.qgis.org/3.16/en/docs/pyqgis_developer_cookbook/index.html) - This should be the go-to for all your basic plugin development needs
* [QGIS API Documentation](https://qgis.org/api/) - Here you'll find Qgis-specific information for the API, endpoints, signals, slots etc.
* [Qt for Python¶](https://doc.qt.io/qtforpython-5/) - Qt is a C++ library so you need to specify the Python docs. This is where you find help with things like QtGui and QtWidgets

## Developing on windows


1. Make a batch file on your desktop to launch VSCode with the QGIS development paths and environment

fill in paths where appropriate

```batch
@echo off
@REM First one needs an explicit path
call "C:\Program Files\QGIS 3.18\bin\o4w_env.bat"
call %OSGEO4W_ROOT%\bin\qt5_env.bat
call %OSGEO4W_ROOT%\bin\py3_env.bat

@echo off
path %PATH%;%OSGEO4W_ROOT%\apps\qgis\bin
path %PATH%;%OSGEO4W_ROOT%\apps\Qt5\bin
path %PATH%;%OSGEO4W_ROOT%\apps\Python37\Scripts

rem o4w_env.bat starts with a clean path, so add what you need

set QGIS_PREFIX_PATH=%OSGEO4W_ROOT%:\=/%/apps/qgis
set GDAL_FILENAME_IS_UTF8=YES
rem Set VSI cache to be used as buffer, see #6448
set VSI_CACHE=TRUE
set VSI_CACHE_SIZE=1000000
set QT_PLUGIN_PATH=%OSGEO4W_ROOT%\apps\qgis\qtplugins;%OSGEO4W_ROOT%\apps\qt5\plugins

set PYTHONPATH=%PYTHONPATH%;%OSGEO4W_ROOT%\apps\qgis\python\
set PYTHONPATH=%PYTHONPATH%;%OSGEO4W_ROOT%\apps\qgis\python\qgis
@REM set PYTHONPATH=%PYTHONPATH%;%OSGEO4W_ROOT%\apps\qgis\python\qgis\PyQt

@REM We include local python scripts since this is where pip installs to for ptvsd and pb_tool
path %PATH%;%APPDATA%\Python\Python37\Scripts

pushd %~dp0
call "C:\Users\Matt\AppData\Local\Programs\Microsoft VS Code\bin\code.cmd"
```

2. Download the following plugins in QGIS:

* [Plugin Reloader](https://github.com/borysiasty/plugin_reloader) -- Handy tool to reload all the code for a given plugin so you don't need to close QGIS.
* [First Aid](https://github.com/wonder-sk/qgis-first-aid-plugin) -- Provides Python debugger and replaces the default Python error handling in QGIS. This one is optional but highly recommended. It gives error traces you might not get otherwise and makes QGIS a lot less black-box.
* [Plugin Builder 3](http://g-sherman.github.io/Qgis-Plugin-Builder) -- Creates a QGIS plugin template for use as a starting point in plugin development. Not totally necessary but good to have if you want to build plugins.




Useful stuff

https://docs.qgis.org/testing/en/docs/pyqgis_developer_cookbook/communicating.html

``` python
from qgis.core import Qgis
iface.messageBar().pushMessage("Error", "I'm sorry Dave, I'm afraid I can't do that", level=Qgis.Critical)
# https://docs.qgis.org/testing/en/docs/pyqgis_developer_cookbook/communicating.html
```

clone this repo to `qrave_toolbar_dev` so that `qrave_toolbar` is what gets used for deployment