FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy and install dependencies
COPY setup/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app ./app
COPY database ./database

# Copy environment file (setup/.env)
COPY setup/.env ./.env

# Expose port
EXPOSE 8000

# Command to run the app with reload
CMD ["uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]