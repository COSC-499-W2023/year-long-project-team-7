#bash
sudo systemctl start docker
docker start capstone-postgres
source venv/bin/activate
cd app
pip install -r requirements.txt
cd capstone 
python manage.py migrate
python manage.py runserver

