## Structure

### Purchasing App
This project was originally written for my summer 2025 internship at OCuSOFT.

This is the root directory for the Purchasing App. Subdirectories are Python projects.

See the individual README's in each repo for details on how to set up environment variables, run tests and build individual Docker images.

### Dashboard Data API

Contains the API to fetch data from the database, including model training. Built on FastAPI.

### Purchasing Dashboard

Contains the logic for rendering the dashboard, including logic for fetching data from the API. Built on Dash.

## Secrets

### Configuring secrets

To set the secrets, run

```
docker secret create dashboard_secrets dashboard_secrets.json
docker secret create api_secrets api_secrets.json
``` 

where `*_secrets.json` is a JSON dictionary that contains the relevant secret names as keys and their values as values. 
Refer to the [docker-compose](./docker-compose.yml) file for details.

You can find the expected values in the [dashboard](Purchasing%20Dashboard/README.md#setup) and [API](Dashboard%20Data%20API/README.md#setup) READMEs, respectively.


### Optional secrets

Customarily, in both projects, secrets are managed by Docker. This has a [number of benefits](https://docs.docker.com/engine/swarm/secrets/). 

However, in Portainer's Docker Standalone environments, containers are manually managed by Portainer's agent via `docker-compose`, and secrets are not supported in a particularly ergonomic way. If deploying to this kind of environment, set the requisite secrets as environment variables, and set the `GET_SECRETS_FROM_ENVIRONMENT_VARIABLES` variable to `True`. 

## Building Alpha End-to-End

Make sure the relevant your `.env` files are set. Also make sure your [secrets](#secrets) are set. Check in the respective package folders for what environment variables are expected, and check in `docker-compose.yml` that your `.env` file is being used to run the image.

Assuming you have `docker` and `docker-compose`: 

First, build the images:

```
docker buildx bake api
docker buildx bake dashboard
```

Then, pull up the "alpha" profile:

```
docker-compose --profile alpha up
```

The API docs will be running on http://localhost:8000/docs,
and the dashboard will be running on http://localhost:8050.

## Deploying to production

See the notes about deploying to Portainer.