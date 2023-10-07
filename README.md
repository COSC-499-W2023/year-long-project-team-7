# Ai Content transformer

## Project setup

### Requirements

-   [Docker](https://www.docker.com/)
-   [Virtualenv](https://pypi.org/project/virtualenv/)
    ```
    pip install virtualenv
    # or
    pip3 install virtualenv
    ```

<br>

### Running dev environment

The following commands must be executed within the `app` directory.

1. **Build and run docker image:**

    These commands only have to be done once for initial setup.

    ```
    docker build -t capstone-postgres .
    docker run --name capstone-postgres -p 5432:5432 -d capstone-postgres
    ```

    To run the container after initial build, you can start it in docker desktop GUI or run:

    ```
    docker run capstone-postgres
    ```

2. **Setup virtual environment**

    This is so that our python environment only contains the dependencies that the project needs.

    ```
    virtualenv venv

    . venv/bin/activate

    pip3 install -r requirements.txt
    ```

    On Windows run this instead:

    ```
    virtualenv venv

    venv\Scripts\activate

    pip install -r requirements.txt
    ```

3. **Go into Django project**

    ```
    cd capstone
    ```

4. **Django migrations**

    Django uses 'models' to interact with the database. Each model represents a table. These commands update the postgres database so that all models are correctly represented.

    ```
    python3 manage.py makemigrations
    python3 manage.py migrate
    ```

5. **Create a Django superuser**

    This will allow you to log into the admin page of the django app.

    It will ask you to create a username and password.

    You can skip the emaiil

    ```
    python3 manage.py createsuperuser
    ```

6. Start Django server
    ```
    python3 manage.py runserver
    ```
7. All done! You can now access the site through your browser.

    Site: http://127.0.0.1:8000/

    Admin panel: http://127.0.0.1:8000/admin

### Optional stuff

#### [Beekeeper Studio](https://github.com/beekeeper-studio/beekeeper-studio/releases/tag/v3.9.20)

-   Gives nice GUI to interact with relational databases
-   Allows running sql queries on the database
-   We can use it to look at the tables in our postgres database
