#!/bin/bash

set -e

echo "Initializing project..."

echo  "pulling code latest changes"
git pull origin master

echo "activating environment"
source .venv/bin/activate

echo "Running sync"
uv sync

cd  backend

echo "Running Migrations"
uv run manage.py migrate --noinput

echo "Collecting static files"
uv run manage.py collectstatic --noinput

echo "Running services"
services='nginx gunicorn skills4hire-worker skills4hire-beat'

for service in $services
do
  echo "Starting $service"
  sudo systemctl restart "$service"
done

echo " Deployment successfully..."





