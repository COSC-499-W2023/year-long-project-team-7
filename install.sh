virtualenv venv
. venv/bin/activate
mkdir app/capstone/files
cp slide-templates/* app/capstone/files
cp app/capstone/transformer/static/img/default_pfp.jpg app/capstone/files
cd app
docker build -t capstone-postgres .
docker run --name capstone-postgres -p 5432:5432 -d capstone-postgres
docker start capstone-postgres
pip install -r requirements.txt
cd capstone
python manage.py migrate
python seed.py
python manage.py runserver