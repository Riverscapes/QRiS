# QGIS Riverscapes Studio (QRiS)

Users, please visit [QRiS website](https://qris.riverscapes.net) for help, documentation and installation instructions. QRiS is installed from the QGIS Plugins Library.  

# Developers
***NB: Be sure to develop in VSCode by opening the relevant Workspace***

* `Workspaces\RIPTOSXDev copy.code-workspace`
* `Workspaces\RIPTWindowsDev.code-workspace`

## Development resources

* [PyQGIS Developer Cookbook](https://docs.qgis.org/3.16/en/docs/pyqgis_developer_cookbook/index.html) - This should be the go-to for all your basic plugin development needs
* [QGIS API Documentation](https://qgis.org/api/) - Here you'll find Qgis-specific information for the API, endpoints, signals, slots etc.
* [Qt for Python](https://doc.qt.io/qtforpython-5/) - Qt is a C++ library so you need to specify the Python docs. This is where you find help with things like QtGui and QtWidgets

## Both windows and OSX:

In order to develop this module live in QGIS you need to clone this repo to the folder where QGIS Stores its plugins. 

* On windows it's something like: `C:\Users\USERNAME\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins`
* On OSX it's something like: `/Users/USERNAME/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins`

## On OSX

You actually have two options when cloning the repo; You can clone the repo directly into you QGIS plugins folder, as described above, or you can clone it anywhere you want and put a ssym link to the repo in your plugins folder. The latter approach gives you more control. The command to create the sym link is:

```bash
ln -s /PATH_TO_CLONED_REPO/QRiS /Users/USER_NAME/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/
```

Note the absence of a trailing slash on the first path and the presence of one on the latter. You know the sym link is working if you can click the symb link in Finder and get redirected to the cloned repo.

Before you start you need to set an environment variable to tell VSCode where QGIS's version of python is. This will depend on which shell you're using (The default is bash but we tend to use zsh)

1. You need to add the following line at the bottom of your `~/.bashrc` or `~/.zshrc` file:

```bash
export QGIS_PATH=/Applications/QGIS.app
```

***NOTE: This path must not end in a slash and must match what's on your system. If you're using the LTR version of QGIS this path might be something like `/Applications/QGIS-LTR.app`***

After this is done you need to restart VSCode completely (not just relloading the window).

2. You need this user setting to be on (it's in the user settings preferences)

```json
"terminal.integrated.allowWorkspaceConfiguration": true
```

3. Open up the `Workspaces/OSXDev.code-workspace` using VSCode. This file contains all the right environment variables necessary to find and work with QGIS python libraries.

4. Debugging the plugin in Visual Studio Code requires `ptvsd` be pip installed **in the version of Python being used by QGIS**.


## Developing on Windows

You will need to launch VSCode with a number of environment variables set so that the right versions of python and its modules can be located.

Make a batch file on your desktop to launch VSCode with the QGIS development paths and environment

fill in paths where appropriate (any of the `C:\` paths below will need to match what's on your system)

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

## Windows AND OSX: Download the following plugins in QGIS:

* [Plugin Reloader](https://github.com/borysiasty/plugin_reloader) -- Handy tool to reload all the code for a given plugin so you don't need to close QGIS when you make code changes.
* [First Aid](https://github.com/wonder-sk/qgis-first-aid-plugin) -- Provides Python debugger and replaces the default Python error handling in QGIS. This one is optional but highly recommended. It gives error traces you might not get otherwise and makes QGIS a lot less black-box.
* [debugvs](https://github.com/lmotta/debug_vs_plugin/wiki) -- This plugin is for debugging in Visual Studio ( tested in Visual Studio Code).
For use, run this plugin and enable the Debug (Python:Attach) in Visual Studio. Need install the ptvsd's module(pip3 install ptvsd). On OSX you can run the following in the terminal to install ptvsd:
``` /Applications/QGIS.app/Contents/MacOS/bin/pip3 install ptvsd ```

* [Plugin Builder 3](http://g-sherman.github.io/Qgis-Plugin-Builder) -- Creates a QGIS plugin template for use as a starting point in plugin development. Not totally necessary but good to have if you want to build plugins. (this one is optional but it's really handy)



### Useful stuff

This part of the cookbook about logging is really useful:

https://docs.qgis.org/testing/en/docs/pyqgis_developer_cookbook/communicating.html

``` python
from qgis.core import Qgis
iface.messageBar().pushMessage("Error", "I'm sorry Dave, I'm afraid I can't do that", level=Qgis.Critical)
# https://docs.qgis.org/testing/en/docs/pyqgis_developer_cookbook/communicating.html
```

clone this repo to `qris_toolbar_dev` so that `qris_toolbar` is what gets used for deployment
