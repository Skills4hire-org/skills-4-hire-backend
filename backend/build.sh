#!/bin/bash

set -e

echo "Initializing project..."

echo "Checking for model changes..."
python3 manage.py makemigrations --noinput

# 2. Apply migrations
echo "Applying database migrations..."
if python3 manage.py migrate --noinput; then
    echo "SUCCESS: Migrations applied."
else
    echo "ERROR: Failed to apply migrations. Exiting."
    exit 1
fi

# Start celery worker and beat before running server
echo Starting celery worker...
celery -A config worker --loglevel=info &

echo Starting Celery Beat....
celery -A config beat --logleve=info &
# 3. Start the server
# Using exec ensures the Django process receives OS signals (like SIGTERM) directly
echo "--> Starting development server on port 8000..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --worker 2





