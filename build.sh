#!/bin/bash

set -e

echo "Initializing project..."

echo  "pulling code latest changes"
git pull origin master

echo "activating environment"
source  .venv/bin/activate

echo "Running sync"
uv sync

cd  backend

echo "Running Migrations"
uv run manage.py migrate

echo "Collecting static files"
uv run manage.py collectstatic --noinput

echo "--> Starting server..."
sudo systemctl restart skills_for_hire_gunicorn

echo " Deployment successfull..."





