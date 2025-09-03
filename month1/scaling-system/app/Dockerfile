FROM python:3.11-slim-bookworm AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set the working directory
WORKDIR /app

# Copy dependency files first to leverage Docker's cache
COPY pyproject.toml uv.lock ./

# Install dependencies into a virtual environment using uv
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev

# Copy the rest of the application
COPY . /app

# Stage 2: Create the final, lean production image
FROM python:3.11-slim-bookworm AS final

# Set the working directory
WORKDIR /app

# Copy the virtual environment and application code from the builder stage
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app /app

# Ensure the virtual environment's bin directory is in the PATH
ENV PATH="/app/.venv/bin:$PATH"
# Ensure the virtual environment's bin directory is in the PATH
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/.venv/lib/python3.11/site-packages"

# Expose the port the application will run on
EXPOSE 8000

# Run the application with a production-grade server (uvicorn)
CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]