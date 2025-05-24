FROM python:3.10-slim-buster

# Set environment variables to reduce Python memory usage
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONHASHSEED=random
ENV PYTHONOPTIMIZE=1
ENV TF_CPP_MIN_LOG_LEVEL=2

# Set the port for Cloud Run
ENV PORT=8080

# Set the working directory
WORKDIR /heart-rate-app

# Copy requirements first for caching
COPY requirements.txt requirements.txt

# Install dependencies (REMOVE gunicorn from requirements.txt)
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Use Flask's built-in server instead of Gunicorn
CMD exec python app.py