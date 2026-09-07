@echo off
setlocal
python -m PyInstaller --clean --noconsole --onefile --name "Gaming Dads Server Manager" --icon "assets\aska_manager_icon.ico" --add-data "assets\aska_manager_icon.png;assets" aska_server_manager.py
endlocal
