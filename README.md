# Platonix: Ai Content transformer

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

### Setup dev environment

**Take note of what directory each command is being executed in**

1. **Build and run docker image:**

    These commands only have to be done once for initial setup.

    ```
    /year-long-project-team-7/app$

    docker build -t capstone-postgres .
    docker run --name capstone-postgres -p 5432:5432 -d capstone-postgres
    ```

    To run the container after initial build, you can start it in docker desktop GUI or run:

    ```
    docker start capstone-postgres
    ```

2. **Setup virtual environment**

    This is so that our python environment only contains the dependencies that the project needs.

    ```
    /year-long-project-team-7/app$

    virtualenv venv
    . venv/bin/activate
    pip install -r requirements.txt
    ```

    On Windows run this instead:

    ```
    /year-long-project-team-7/app$
    virtualenv venv
    . venv\Scripts\activate
    pip install -r requirements.txt
    ```

3. **Set up pre-commit hooks**

    The pre-commit hooks run checks every time you try to do a commit.

    These also run on gitHub so running them locally allows us to find issues before push.

    1. Format code with black (python) and djlint (html)
    2. Run mypy to check correct typing
    3. Run tests

    **If the checks fail, you cannot commit.**

    This command will install the pre-commit hooks found in `.pre-commit-config.yaml` into your local git repository.

    ```
    /year-long-project-team-7$

    pre-commit install
    ```

4. **Environment variables**
    - Create copy of `settings_env_example.py` and update the new file with your keys.
    - Rename your new file to `settings_env.py`.
5. **Django migrations**

    Django uses 'models' to interact with the database. Each model represents a table. These commands update the postgres database so that all models are correctly represented.

    ```
    /year-long-project-team-7/app/capstone$

    python3 manage.py makemigrations
    python3 manage.py migrate
    ```

6. **Create a Django superuser (Optional)**

    This will allow you to log into the admin page of the django app.

    It will ask you to create a username and password.

    You can skip the email

    ```
    /year-long-project-team-7/app/capstone$

    python3 manage.py createsuperuser
    ```

7. **Start Django server**

    ```
    /year-long-project-team-7/app/capstone$

    python3 manage.py runserver
    ```

8. **Setting up Stripe**

    ```
    /year-long-project-team-7/app/capstone$

    Setting up Stripe:

    0. Update your settings_env with the stripe keys

    1. Install using instructions in the "apt" tab https://stripe.com/docs/stripe-cli

    2. Log in with API webhook key (found in accounts sheet) ```stripe login --api-key [key here]```

    3. Run ```stripe listen --forward-to localhost:8000/webhook```

    4. Run migrations

    5. At this point you should be able to test buying a subscription with a fake credit card
    ```
    

10. **All done!**

    You can now access the site through your browser.

    Site: http://127.0.0.1:8000/

    Admin panel: http://127.0.0.1:8000/admin

### Optional stuff

#### [Beekeeper Studio](https://github.com/beekeeper-studio/beekeeper-studio/releases/tag/v3.9.20)

-   Gives nice GUI to interact with relational databases
-   Allows running sql queries on the database
-   We can use it to look at the tables in our postgres database

<br>
<hr>

## Database Design

[View on dbdiagram.io](https://dbdiagram.io/d/Capstone-651f4dbcffbf5169f023111f)

![Image](https://github.com/COSC-499-W2023/year-long-project-team-7/assets/71345367/34576831-7193-46e8-9c9f-5e1fb650138c)
