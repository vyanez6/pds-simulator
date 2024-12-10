@echo off
rem To install the pds simulator

if exist ".\venv\" (
  echo Virtual environment already available
) else (
  echo Creating virtual environment
  python -m venv .\venv
)

echo.
echo Installing requirements
.\venv\Scripts\pip.exe install -r requirements.txt

if exist ".\venv\Scripts\flask.exe" (
  echo Installation successful!
) else (
  echo Unable to find flask executable. Installation failed
)
