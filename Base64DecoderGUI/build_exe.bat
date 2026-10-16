@echo off
setlocal
cd /d "%~dp0"

echo ==========================================
echo Building Base64 Decoder EXE
echo ==========================================

where py >nul 2>nul
if %errorlevel%==0 (
    set PY=py
) else (
    set PY=python
)

%PY% -m pip install --upgrade pip
if errorlevel 1 goto :error

%PY% -m pip install -r requirements.txt
if errorlevel 1 goto :error

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist Base64Decoder.spec del /q Base64Decoder.spec

%PY% -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --onefile ^
  --windowed ^
  --name Base64Decoder ^
  base64_decoder_gui.py

if errorlevel 1 goto :error

echo.
echo Build successful.
echo EXE: %CD%\dist\Base64Decoder.exe
pause
exit /b 0

:error
echo.
echo Build failed.
pause
exit /b 1
