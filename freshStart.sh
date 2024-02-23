#bash
rm -rf app/capstone/files/*
cp slide-templates/* app/capstone/files
docker start capstone-postgres
source venv/bin/activate
cd app
pip install -r requirements.txt
cd capstone
python seed.py
python manage.py migrate
python manage.py runserver

