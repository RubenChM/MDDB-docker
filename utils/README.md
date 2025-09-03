# Utils

This service acts as a hodgepodge of utilities.

## Dockerfile

```Dockerfile
# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (minimal)
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir pymongo

# Create scripts directory
RUN mkdir -p /app/scripts

# Copy Python scripts
COPY scripts/ /app/scripts/

# Copy entry script
COPY entrypoint.sh /app/entrypoint.sh

# Make scripts executable
RUN chmod +x /app/scripts/*.py /app/entrypoint.sh

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Create a non-root user
RUN useradd -m -u 1000 scriptuser && chown -R scriptuser:scriptuser /app
USER scriptuser

# Entry script handles command execution
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command shows help
CMD ["help"]
```
