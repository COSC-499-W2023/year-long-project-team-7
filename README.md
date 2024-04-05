<a href="https://platonix.app"><img src="app/capstone/transformer/static/img/favicon-purple.png" width="100"></img></a>

https://platonix.app

# Platonix: Ai Content transformer

Platonix is an Ai Powered tool that allows users to generate Powerpoint Presentations and exercises.

## Requirements

These **_must_** be installed

-   [Docker](https://www.docker.com/)
-   [Python](https://www.python.org/downloads/)
    -   [Virtualenv](https://pypi.org/project/virtualenv/)

You **_must_** have API keys for the following for full functionaliy

-   [SerpApi](https://serpapi.com/manage-api-key)
-   [OpenAi](https://platform.openai.com/api-keys)
-   [Stripe](https://dashboard.stripe.com/apikeys) (app will work without it but store will be broken)
-   [Gmail](https://support.google.com/mail/answer/185833?hl=en) (app will work withouth it but account creation/recovery wont work)

## Quickstart

1. **Environment Variables**

    Copy the file [settings_env_example.py](app/capstone/capstone/settings_env_example.py) to [settings_env.py](app/capstone/capstone/settings_env.py)

    Linux/MacOS

    ```
    cp app/capstone/capstone/settings_env_example.py app/capstone/capstone/settings_env.py
    ```

    Windows

    ```
    copy app\capstone\capstone\settings_env_example.py app\capstone\capstone\settings_env.py
    ```

    Copy all of your API keys into [settings_env.py](app/capstone/capstone/settings_env.py)

1. **Easy Install (without stripe checkout)**

    **Docker desktop must be running**

    Linux/MacOS

    ```
    ./install.sh
    ```

    Windows

    ```
    cmd /c install.bat
    ```

    App should be running locally now.

    Login with

    Email:`user@email.com`

    Password:`password`

### More details for developing can be found in our [Developing Guide](DEVELOPING.md).
