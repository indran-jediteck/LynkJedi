FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create a .env file with default values
# These will be overridden by environment variables if provided
RUN echo "MONGO_URI=mongodb://mongo:27017" > .env && \
    echo "MONGO_DB=lynkjedi_db" >> .env && \
    echo "SMTP_SERVER=smtp.example.com" >> .env && \
    echo "SMTP_PORT=587" >> .env && \
    echo "SMTP_USERNAME=" >> .env && \
    echo "SMTP_PASSWORD=" >> .env && \
    echo "EMAIL_FROM=noreply@example.com" >> .env

# Expose the port the app runs on
# Default to 8001 but Cloud Run will override with PORT env var
EXPOSE 8080

# Command to run the application
# Use uvicorn directly with the PORT environment variable
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}
