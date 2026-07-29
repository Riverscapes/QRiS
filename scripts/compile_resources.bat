@echo off
REM Compile Qt resources for QGIS 3 (Qt5) and QGIS 4 (Qt6).
REM Tries pyrcc5 first (QGIS 3), then pyrcc6 (QGIS 4), then falls back
REM to running pyrcc5 from QGIS 3.40.8 with the correct PATH.
REM After compilation, rewrites the PyQt5/Qt6 import to use the
REM version-independent qgis.PyQt wrapper.

cd /d "%~dp0.."

REM 1. Try pyrcc5 on PATH (QGIS 3)
where pyrcc5 >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo Using pyrcc5...
    pyrcc5 src/resources.qrc -o src/resources.py
    if %ERRORLEVEL% equ 0 goto :post_process
)

REM 2. Try pyrcc6 on PATH (QGIS 4)
where pyrcc6 >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo Using pyrcc6...
    pyrcc6 src/resources.qrc -o src/resources.py
    if %ERRORLEVEL% equ 0 goto :post_process
)

REM 3. Try pyrcc5 from QGIS 3.40.8 with full environment
set "QGIS3_ROOT=C:\Program Files\QGIS 3.40.8"
if exist "%QGIS3_ROOT%\apps\Python312\Scripts\pyrcc5.exe" (
    echo Using pyrcc5 from QGIS 3.40.8...
    set "PATH=%QGIS3_ROOT%\apps\Qt5\bin;%QGIS3_ROOT%\apps\qgis-ltr\bin;%QGIS3_ROOT%\bin;%QGIS3_ROOT%\apps\Python312\Scripts;%QGIS3_ROOT%\apps\Python312;%PATH%"
    set "PYTHONPATH=%QGIS3_ROOT%\apps\Python312\Lib\site-packages;%PYTHONPATH%"
    pyrcc5 src/resources.qrc -o src/resources.py
    if %ERRORLEVEL% equ 0 goto :post_process
)

echo ERROR: Failed to compile resources.
exit /b 1

:post_process
REM Replace PyQt5/PyQt6 imports with version-independent qgis.PyQt wrapper
REM so the file works on both QGIS 3 (Qt5) and QGIS 4 (Qt6).
REM Also strip the unnecessary UTF-8 coding comment added by pyrcc.
python scripts\post_process_resources.py src\resources.py
echo DONE
