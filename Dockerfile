FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install only what's needed in production
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry globally
RUN pip install --no-cache-dir poetry

# Copy dependency files early for caching
COPY pyproject.toml poetry.lock* ./

# Configure Poetry
RUN poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction --no-ansi

# Copy the rest of the app
COPY . .

# Environment variables for Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Expose Django's default port
EXPOSE 8000

# Default command
CMD ["poetry", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]
