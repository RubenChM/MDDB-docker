#!/bin/bash

# Ensure required environment variables are set
: "${DB_HOST:?MongoDB host not set}"
: "${MONGO_PORT:?MongoDB port not set}"
: "${MONGO_INITDB_DATABASE:?MongoDB initDB not set}"
: "${BACKUP_DIR:?Backup directory not set}"
: "${MONGO_INITDB_ROOT_USERNAME:?Mongo DB root username not set}"
: "${MONGO_INITDB_ROOT_PASSWORD:?Mongo DB root password not set}"

# Wait for MongoDB to be ready before starting first dump
until mongosh "mongodb://${MONGO_INITDB_ROOT_USERNAME}:${MONGO_INITDB_ROOT_PASSWORD}@${DB_HOST}:${MONGO_PORT}/${MONGO_INITDB_DATABASE}?authSource=admin" --eval "db.stats()" >/dev/null 2>&1; do 
  echo "Waiting for MongoDB..."
  sleep 2
done

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Create timestamp
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_PATH="$BACKUP_DIR/$TIMESTAMP"

echo "Starting backup at $(date)"

# Create backup
if ! mongodump --host "$DB_HOST" -u $MONGO_INITDB_ROOT_USERNAME -p $MONGO_INITDB_ROOT_PASSWORD --out "$BACKUP_PATH"; then
    echo "Backup failed!"
    exit 1
fi

echo "Backup completed: $BACKUP_PATH"
