@echo off
rem Wrapper so the cleanup can be started directly from PowerShell/CMD
rem (avoids the Windows .py file-association opening a new window).
rem
rem The Windows Store "python.exe" alias can be a dead App Execution Alias.
rem Probe each candidate by actually running --version and use the first that
rem works: py -3 -> python3 -> explicit WindowsApps python3.exe -> python.
setlocal

set "SCRIPT=%~dp0docker-buildx-cleanup.py"

py -3 --version >nul 2>nul
if not errorlevel 1 goto use_py

python3 --version >nul 2>nul
if not errorlevel 1 goto use_python3

"%LOCALAPPDATA%\Microsoft\WindowsApps\python3.exe" --version >nul 2>nul
if not errorlevel 1 goto use_python3_exe

python --version >nul 2>nul
if not errorlevel 1 goto use_python

echo Kein funktionierender Python-Interpreter gefunden (versucht: py -3, python3, python).
exit /b 9009

:use_py
py -3 "%SCRIPT%" %*
exit /b %errorlevel%

:use_python3
python3 "%SCRIPT%" %*
exit /b %errorlevel%

:use_python3_exe
"%LOCALAPPDATA%\Microsoft\WindowsApps\python3.exe" "%SCRIPT%" %*
exit /b %errorlevel%

:use_python
python "%SCRIPT%" %*
exit /b %errorlevel%
