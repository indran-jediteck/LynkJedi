FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the port the app runs on
# Default to 8001 but Cloud Run will override with PORT env var
EXPOSE 8001

# Command to run the application
# Use the Cloud Run specific entry point
CMD ["python", "-m", "app.cloud_run"]
