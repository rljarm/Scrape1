#!/bin/bash

# Exit on error
set -e

# Function to wait for postgres
wait_for_postgres() {
    echo "Waiting for PostgreSQL..."
    while ! nc -z $DB_HOST $DB_PORT; do
        sleep 0.1
    done
    echo "PostgreSQL started"
}

# Function to wait for redis
wait_for_redis() {
    echo "Waiting for Redis..."
    while ! nc -z $REDIS_HOST 6379; do
        sleep 0.1
    done
    echo "Redis started"
}

# Wait for dependencies
wait_for_postgres
wait_for_redis

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create cache table
echo "Creating cache table..."
python manage.py createcachetable

# Start server
echo "Starting server..."
exec "$@"
