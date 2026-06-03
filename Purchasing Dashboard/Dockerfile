# NOTE: The build context "common" should be set to the directory of the Dashboard Common package"
# to ensure all necessary files are available during the build process.

# Builder stage
FROM python:3.13-slim AS builder

# Set workdir
WORKDIR /app

# Install uv
# COPY --from=ghcr.io/astral-sh/uv:0.8.5 /uv /uvx /bin/
RUN pip install uv

#ENV UV_LINK_MODE=copy \
#    UV_COMPILE_BYTECODE=1 \
    #UV_PYTHON_DOWNLOADS=never \
    #UV_PYTHON=python3.13 \
#    UV_PROJECT_ENVIRONMENT=/app

# Build common library 
COPY --from=common ["./src", "/common_src/src"]
COPY --from=common ["./pyproject.toml", "/common_src/"]
#COPY --from=common . /common_src/

# Copy project files
COPY pyproject.toml /app/

# Install the common library wheel
RUN uv venv
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install /common_src/

# Install the main project dependencies (for docker caching purposes)
RUN sed -i 's/Dashboard Common/common_src/g' /app/pyproject.toml
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-install-project --no-dev   

# Sync again to install the project in non‑editable (production) mode and compile bytecode
#RUN uv sync --locked --no-editable --compile-bytecode

COPY /src /app/src
ENV PYTHONPATH="/app/src:$PYTHONPATH"

RUN uv pip install --no-deps --system .

RUN uv cache clean

EXPOSE 8050
    
CMD ["uv", "run", "gunicorn", "-b", "0.0.0.0:8050", "purchasing_dashboard.app:app"]