@echo off
echo =========================================================
echo Starting Task 1: URL Knowledge Base (Django + DRF + SQLite + FAISS)
echo =========================================================
echo Server starting at http://127.0.0.1:8000/
echo Web UI: http://127.0.0.1:8000/
echo REST API: http://127.0.0.1:8000/api/urls/
echo.
cd ..\task1_knowledge_base
python manage.py migrate --noinput
python manage.py runserver 127.0.0.1:8000
pause
