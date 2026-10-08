@echo off
set PYTHONPATH=%cd%
"%~dp0venv\Scripts\python.exe" -m pytest tests -v
pause
