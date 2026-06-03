# NOTE: The build context "common" should be set to the directory of the Dashboard Common package"
# to ensure all necessary files are available during the build process.

# Download wait-for-it.sh from a known image (e.g., curlimages/curl)
FROM curlimages/curl AS downloader
WORKDIR /tmp
RUN curl -L https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh -o wait-for-it.sh
RUN chmod +x wait-for-it.sh

# --- Stage 1 ---
# Use official Python image with uv pre-installed
FROM python:3.13-slim AS builder

# Set work directory
WORKDIR /build

# Install build tools
RUN pip install uv

# Copy common package and project files
COPY --from=common [".", "/common_src"]
COPY ["./src", "./src"]
COPY ["pyproject.toml", "uv.lock", "./"]

# Add common as a dependency and install all dependencies
RUN uv venv && uv pip install --upgrade pip
RUN uv pip install /common_src/
RUN sed -i 's/Dashboard Common/common_src/g' ./pyproject.toml
RUN uv sync --no-dev --no-install-project 
RUN uv pip install --no-deps --system .


# Build common and the api (creates two wheel files)
RUN uv build /common_src/ --wheel
RUN uv build . --wheel

# --- Stage 2 ---
FROM python:3.13-slim

WORKDIR /app

# Get the wait-for-it.sh script
COPY --from=downloader /tmp/wait-for-it.sh /wait-for-it.sh

# Install the wheels built in the builder stage
COPY --from=builder /common_src/dist/*.whl /wheels/
COPY --from=builder /build/dist/*.whl /wheels/

RUN pip install uv
RUN uv venv
RUN uv pip install /wheels/*.whl --no-cache-dir
RUN uv pip install fastapi uvicorn --no-cache-dir

# Clean up (optional, just to be sure)
RUN rm -rf /root/.cache

# Expose FastAPI port
EXPOSE 8000

# Start FastAPI app on uvicorn

# ENTRYPOINT ["/wait-for-it.sh", "-t", "30", "mock-database:1433", "--", "uv", "run", "uvicorn", "data_api.api_main:app", "--host", "0.0.0.0", "--port", "8000"]

ENTRYPOINT ["uv", "run", "uvicorn", "data_api.api_main:app", "--host", "0.0.0.0", "--port", "8000"]