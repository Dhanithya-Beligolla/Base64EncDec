@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
    py base64_decoder_gui.py
) else (
    python base64_decoder_gui.py
)
