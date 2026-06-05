# Favorit3s

### How to use a simple shortcut that can be docked on system tray.

1) You should have your portable python in the c:\python39 location, then you don't have to edit any files. Otherwise you have to edit the python path in `run.bat`.
2) You have to change the start folder on `favorit3s.lnk` shortcut to the actual folder of the tool on your drive. (Right click and edit start folder)
3) You can drag and drop the `favorit3s.lnk` shortcut to your Windows tray.

### Generate .exe file

`python -m PyInstaller --onefile --windowed --icon=icon.ico favorit3s.py`