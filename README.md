# Ai Content transformer

## Project setup

### Requirements
- [Docker](https://www.docker.com/)
- [Virtualenv](https://pypi.org/project/virtualenv/)
    ```
    pip install virtualenv
    # or
    pip3 install virtualenv
    ```


<br>

### Running dev environment

The following commands must be executed within the `app` directory.

1. **Build and run docker image:** 
    
    The build only has to be done once for initial setup.
    
    You can use the command to run the container every time or use the Docker desktop GUI
    ```
    docker build -t capstone-postgres .
    docker run --name capstone-postgres -p 5432:5432 -d capstone-postgres
    ```
2. **Activate virtual environment**

    This is so that our python environment only contains the dependancies that the project needs

    Also makes setup easier 
    ```
    . env/bin/activate
    # or
    source env/bin/activate
    ```
3. **Go into Django project**
    ```
    cd capstone
    ```

4. **Django migrations**

    Django uses 'models' to interact with the database. Each model represents a table. These commands
    ```
    python3 manage.py makemigrations
    python3 manage.py migrate
    ```
5. Create a django superuser (you can skip the email)
    ```
    python3 manage.py createsuperuser
    ```
6. Start django server
    ```
    python3 manage.py runserver
    ```
7. All done! You can now access the site through your browser.
    
    Site: http://127.0.0.1:8000/ 
    
    Admin panel: http://127.0.0.1:8000/admin

### Optional stuff

#### 