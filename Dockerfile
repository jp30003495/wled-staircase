# Use official Python base image for ARM64
FROM python:3.12-slim

# Set working directory inside container
WORKDIR /app

# Copy and install dependencies first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Expose port the server will run on
EXPOSE 5000

# Command to run your server
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "5000"]
