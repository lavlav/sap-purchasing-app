## Dashboard Data API

This module contains common functions for the Data API and Purchasing Dashboard.

## Testing and Building

Run (from this directory):

```
uv sync --dev
uv pip install -e .
uv run pytest --cov
```

## Deploying

This is just a library package. It is discovered and built by the Dockerfiles of the other 
projects in this monorepo that depend on it.

Therefore, there is nothing to deploy here.