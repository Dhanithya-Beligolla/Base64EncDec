@echo off
setlocal
cd /d "%~dp0"

if not exist "dist\Base64Decoder.exe" (
    echo Base64Decoder.exe was not found.
    echo Building it first...
    call build_exe.bat
    if errorlevel 1 exit /b 1
)

set ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe
if not exist "%ISCC%" set ISCC=C:\Program Files\Inno Setup 6\ISCC.exe

if not exist "%ISCC%" (
    echo.
    echo Inno Setup 6 was not found.
    echo Install Inno Setup 6, then run this file again.
    echo You can install it with:
    echo winget install --id JRSoftware.InnoSetup -e -s winget -i
    pause
    exit /b 1
)

"%ISCC%" "installer.iss"
if errorlevel 1 (
    echo Installer build failed.
    pause
    exit /b 1
)

echo.
echo Installer created in:
echo %CD%\installer_output\Base64Decoder_Setup.exe
pause
