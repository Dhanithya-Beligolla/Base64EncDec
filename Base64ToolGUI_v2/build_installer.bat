@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ==========================================
echo Base64 Tool - Windows Installer Builder
echo ==========================================
echo.

REM -------------------------------------------------------
REM Step 1 - Build Base64Tool.exe if it does not exist
REM -------------------------------------------------------
if not exist "dist\Base64Tool.exe" (
    echo Base64Tool.exe was not found.
    echo Building application EXE first...
    echo.
    call build_exe.bat
    if errorlevel 1 goto BUILD_ERROR
)

REM -------------------------------------------------------
REM Step 2 - Locate Inno Setup compiler
REM -------------------------------------------------------
set "ISCC="

REM Check whether ISCC.exe is already on PATH
for /f "delims=" %%I in ('where ISCC.exe 2^>nul') do set "ISCC=%%I"

if defined ISCC goto FOUND_ISCC

REM Standard 64-bit / 32-bit installation folders
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if defined ISCC goto FOUND_ISCC

if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set "ISCC=C:\Program Files\Inno Setup 6\ISCC.exe"
if defined ISCC goto FOUND_ISCC

REM Common per-user installation locations
if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if defined ISCC goto FOUND_ISCC

if exist "%LOCALAPPDATA%\Inno Setup 6\ISCC.exe" set "ISCC=%LOCALAPPDATA%\Inno Setup 6\ISCC.exe"
if defined ISCC goto FOUND_ISCC

REM Winget packages can also live under Microsoft\WinGet\Packages.
for /f "delims=" %%I in ('where /r "%LOCALAPPDATA%\Microsoft\WinGet\Packages" ISCC.exe 2^>nul') do set "ISCC=%%I"
if defined ISCC goto FOUND_ISCC

REM Last-resort search inside LOCALAPPDATA.
for /f "delims=" %%I in ('where /r "%LOCALAPPDATA%" ISCC.exe 2^>nul') do set "ISCC=%%I"
if defined ISCC goto FOUND_ISCC

goto ISCC_NOT_FOUND


:FOUND_ISCC
echo Found Inno Setup compiler:
echo "%ISCC%"
echo.

REM -------------------------------------------------------
REM Step 3 - Compile installer.iss
REM -------------------------------------------------------
if not exist "installer.iss" (
    echo ERROR: installer.iss was not found in:
    echo %CD%
    goto FAIL
)

"%ISCC%" "installer.iss"

if errorlevel 1 goto INSTALLER_ERROR

echo.
echo ==========================================
echo SUCCESS
echo ==========================================
echo.
echo Windows installer was created successfully.
echo.
echo Expected output folder:
echo %CD%\installer_output
echo.
dir /b "installer_output\*.exe" 2>nul
echo.
pause
exit /b 0


:ISCC_NOT_FOUND
echo.
echo ERROR: Inno Setup is installed, but ISCC.exe could not be found automatically.
echo.
echo Run this command:
echo.
echo where /r "%LOCALAPPDATA%" ISCC.exe
echo.
echo If that does not find it, run:
echo.
echo where /r "C:\Program Files" ISCC.exe
echo.
echo Then copy the returned ISCC.exe path.
echo.
pause
exit /b 1


:BUILD_ERROR
echo.
echo ERROR: Base64Tool.exe build failed.
echo Check the errors shown by build_exe.bat.
echo.
pause
exit /b 1


:INSTALLER_ERROR
echo.
echo ERROR: Inno Setup failed to compile installer.iss.
echo Review the compiler error shown above.
echo.
pause
exit /b 1


:FAIL
echo.
pause
exit /b 1
