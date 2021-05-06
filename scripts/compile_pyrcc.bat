@echo off
echo Compiling...
python3 -m PyQt5.pyrcc_main src/resources.qrc -o src/resources.py

python3 -m PyQt5.pyuic src/ui/about_dialog.ui -o src/ui/aboot.py 
echo DONE
