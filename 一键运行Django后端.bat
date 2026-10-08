@echo off
cd /d "%~dp0django_backend"
..\venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
pause
