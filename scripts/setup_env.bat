@echo off
echo =========================================================
echo Setting up Technical Assignment - Round 2 Environment
echo =========================================================
python -m pip install --upgrade pip
pip install -r requirements.txt
cd task1_knowledge_base
python manage.py makemigrations harvester
python manage.py migrate
cd ..
echo.
echo Environment setup completed successfully!
pause
