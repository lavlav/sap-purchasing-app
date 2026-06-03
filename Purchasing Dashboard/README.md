## Purchasing App

A dashboard for purchasing departments in companies that rely on SAP B1.

This dashboard was originally a port of Purchasing_App (R) to Python.

Icons from [Feather](https://github.com/feathericons).

## Project Structure

```
Purchasing Dashboard
├── Dockerfile
├── file_watcher.py                 # Utility for double-checking reloader
├── README.md                       # This file
├── src
│   └── purchasing_dashboard    # App source folder
│       ├── __init__.py                 # Module specifier, empty
│       ├── app.py                      # Entrypoint
│       ├── assets                      # Static files to be served with the app
│       ├── callbacks                   # Dash callbacks
│       ├── layout                      # Page layout subcomponents
│       ├── pages                       # Dash page layout
│       └── utils                       # Utility functions
└── tests                           # Tests folder
```

## Running

### Setup

The following [secrets](../README.md#secrets) need to be set:

* `BASIC_AUTH_USERNAME` A string providing a username to access the dashboard via HTTP Basic Auth
* `BASIC_AUTH_PASSWORD` A string providing a password to access the dashboard via HTTP Basic Auth
* `API_URL` The URL that Dashboard Data API runs on. Remember to include port number.

The following environment variables need to be set:

* `DEBUG_ENABLED` True if the dashboard should run in Debug mode, false otherwise

The following environment variables are optional:

* `LOG_LEVEL` One of DEBUG, INFO, WARN, ERROR, CRITICAL. Controls what type of logs are emitted.
* `GET_SECRETS_FROM_ENVIRONMENT_VARIABLES` See the [optional secrets](../README.md#optional-secrets) section.

### Commands

Once everything has been set, run (from this directory):

```
uv sync --dev
uv add --editable ../"Dashboard Common"
uv pip install -e .
```

Then:

```
uv run python src/purchasing_dashboard/app.py
```

To run tests instead:

```
uv run pytest --cov
```

## Deploying

See [the base README](../README.md#deploying-to-production).