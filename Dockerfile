FROM python:3.10-slim-buster

# Set environment variables to reduce Python memory usage
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONHASHSEED=random
ENV PYTHONOPTIMIZE=1
# Add to your Dockerfile
ENV TF_FORCE_GPU_ALLOW_GROWTH=true
ENV TF_CPP_MIN_LOG_LEVEL=2

# Set the port for Cloud Run
ENV PORT=8080

# Set the working directory
WORKDIR /heart-rate-app

# Copy requirements first for caching
COPY requirements.txt requirements.txt

# Install dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Command to run the application
CMD exec gunicorn --bind :$PORT --workers 1 --threads 2 app:app