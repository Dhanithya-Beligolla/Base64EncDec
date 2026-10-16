@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (set PY=py) else (set PY=python)
%PY% -m pip install -r requirements.txt
if errorlevel 1 goto :err
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
%PY% -m PyInstaller --noconfirm --clean --onefile --windowed --name Base64Tool base64_tool_gui.py
if errorlevel 1 goto :err
echo.
echo EXE created: %CD%\dist\Base64Tool.exe
pause
exit /b 0
:err
echo Build failed.
pause
exit /b 1
