@echo off
setlocal
title Maitri - Start and Repair Audio Dependencies
cd /d "%~dp0"

echo ================================================
echo Maitri - checking the correct Python environment
echo ================================================
echo.
py -3.14 --version
if errorlevel 1 (
    echo ERROR: Python 3.14 was not found by the Windows Python launcher.
    echo Run "py -0p" in Command Prompt and send me the output.
    pause
    exit /b 1
)

echo.
echo Installing/checking Maitri audio dependencies for Python 3.14...
py -3.14 -m pip install sounddevice numpy vosk pyttsx3
if errorlevel 1 (
    echo.
    echo ERROR: Package installation failed. Read the error above.
    pause
    exit /b 1
)

echo.
echo Verifying microphone and speech packages...
py -3.14 -c "import sounddevice, numpy, vosk, pyttsx3; print('Maitri audio packages OK')"
if errorlevel 1 (
    echo.
    echo ERROR: Python 3.14 still cannot import an audio package.
    pause
    exit /b 1
)

echo.
echo Starting Maitri with Python 3.14...
echo Keep this window open while Maitri runs.
echo.
py -3.14 app.py
if errorlevel 1 (
    echo.
    echo Maitri exited with an error. Read the message above.
    pause
)
endlocal
