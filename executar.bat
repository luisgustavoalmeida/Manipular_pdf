@echo off
cd /d "%~dp0"
"%~dp0venv\Scripts\python.exe" "%~dp0main.py"
REM Para usar o menu em terminal: python main.py --console
pause
