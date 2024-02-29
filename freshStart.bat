@echo off
del /Q app\capstone\files\*
copy slide-templates\* app\capstone\files
copy app\capstone\transformer\static\img\default_pfp.jpg app\capstone\files
docker start capstone-postgres
call venv\Scripts\activate
cd app
pip install -r requirements.txt
cd capstone
python manage.py migrate
python seed.py
python manage.py runserver
