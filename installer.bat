@echo off
REM SensAI - installation (a lancer une seule fois)
cd /d "%~dp0"
set PYEXE=
where py >nul 2>nul && set PYEXE=py -3
if not defined PYEXE (where python >nul 2>nul && set PYEXE=python)
if not defined PYEXE (
  echo Python n'est pas installe. Installez Python 3.11+ depuis https://www.python.org/downloads/
  echo en cochant "Add python.exe to PATH", puis relancez ce fichier.
  pause
  exit /b 1
)
%PYEXE% scripts\installer.py %*
pause
