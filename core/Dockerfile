FROM python:3.9-slim

WORKDIR /netnews/core

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY main.py .

# Environment variables should be provided at runtime or through .env file
# Do not hardcode sensitive information like API keys in Dockerfile

# Run the application
CMD ["python", "main.py"]
