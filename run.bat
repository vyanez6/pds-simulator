@echo off
if exist ".\venv\" (
  .\venv\Scripts\flask --app pdsim run --port 9070 --host=0.0.0.0
) else (
  echo Virtual environment not created. Run install.bat first
)
