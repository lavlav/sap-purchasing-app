## Dashboard Data API

This is the Python backend API for the Purchasing App, built on the FastAPI framework.

## Running

### Setup

The following [secrets](../README.md#secrets) must be set:

* `HISTORICAL_DATABASE_URL` A [SQLAlchemy database URL](#database-urls) for the historical database/data warehouse.
* `SAP_DATABASE_URL` A SQLAlchemy database URL for the SAP Business One database.

The following environment variables are optional:

* `TFC_API_KEY` The API key provided by [The Forecasting Company](https://docs.retrocast.com/). If not provided, the forecasting option that provides it will be disabled.
* `LOG_LEVEL` One of DEBUG, INFO, WARN, ERROR, CRITICAL. Controls what type of logs are emitted.
* `GET_SECRETS_FROM_ENVIRONMENT_VARIABLES` See the [optional secrets](../README.md#optional-secrets) section.

### Commands

Once everything has been set, run (from this directory):

```
uv sync --dev --locked
uv add --editable ../"Dashboard Common"
uv run fastapi dev ./src/data_api/api_main.py
```

### Database URLs

If you're confused on structure, see the [SQLAlchemy documentation](https://docs.sqlalchemy.org/en/20/core/engines.html#database-urls).

Because this URL can potentially contain the password for the service account, it is treated as a Docker secret.

For this project, the dialect + driver prefix should be `mssql-pymssql`.

## Deploying

See [the base README](../README.md#deploying-to-production).