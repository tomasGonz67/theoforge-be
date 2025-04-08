#!/bin/bash
set -e

# Function to attempt database migration with retries
function migrate_database() {
  local max_retries=5
  local retry_wait=5
  local retries=0
  local migration_successful=false

  echo "Attempting database migrations..."
  
  while [ $retries -lt $max_retries ]; do
    if alembic upgrade head; then
      echo "Database migrations completed successfully!"
      migration_successful=true
      break
    else
      retries=$((retries + 1))
      echo "Migration attempt $retries failed. Retrying in $retry_wait seconds..."
      sleep $retry_wait
    fi
  done

  if [ "$migration_successful" != true ]; then
    echo "Failed to run database migrations after $max_retries attempts."
    echo "The application will start anyway, but some features may not work correctly."
  fi
}

# Run database migrations
migrate_database

# Start the FastAPI application
echo "Starting the FastAPI application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload 