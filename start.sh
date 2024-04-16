#bash
source venv/bin/activate
cd app/capstone
python manage.py migrate
python manage.py runserver

