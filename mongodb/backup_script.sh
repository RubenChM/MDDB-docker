#!/bin/bash

# Ensure required environment variables are set
: "${DB_HOST:?MongoDB host not set}"
: "${MONGO_PORT:?MongoDB port not set}"
: "${MONGO_INITDB_DATABASE:?MongoDB initDB not set}"
: "${BACKUP_DIR:?Backup directory not set}"
: "${RETENTION_COUNT:?Retention days not set}"
: "${BACKUP_INTERVAL:?Backup interval not set}"
: "${MONGO_INITDB_ROOT_USERNAME:?Mongo DB root username not set}"
: "${MONGO_INITDB_ROOT_PASSWORD:?Mongo DB root password not set}"

# Wait for MongoDB to be ready before starting first dump
until mongosh "mongodb://${MONGO_INITDB_ROOT_USERNAME}:${MONGO_INITDB_ROOT_PASSWORD}@${DB_HOST}:${MONGO_PORT}/${MONGO_INITDB_DATABASE}?authSource=admin" --eval "db.stats()" >/dev/null 2>&1; do 
  echo "Waiting for MongoDB..."
  sleep 2
done

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

while true; do
    # Create timestamp
    TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
    BACKUP_PATH="$BACKUP_DIR/$TIMESTAMP"
    
    echo "Starting backup at $(date)"
    
    # Create backup
    if ! mongodump --host "$DB_HOST" -u $MONGO_INITDB_ROOT_USERNAME -p $MONGO_INITDB_ROOT_PASSWORD --out "$BACKUP_PATH"; then
        echo "Backup failed! Retrying after $BACKUP_INTERVAL seconds"
        sleep "$BACKUP_INTERVAL"
        continue
    fi
    
    # Compress backup
    tar -czf "$BACKUP_PATH.tar.gz" -C "$BACKUP_PATH" .
    rm -rf "$BACKUP_PATH"
    
    echo "Backup completed: $BACKUP_PATH.tar.gz"
    
    # Rotational cleanup
    echo "Applying retention policy (keeping $RETENTION_COUNT last backups)"
    # Remove backups older than the retention period
    (cd "$BACKUP_DIR" && ls -tp | grep -v '/$' | tail -n +$(($RETENTION_COUNT + 1)) | xargs -I {} rm -- {})
    cd /
    
    # Wait for next backup
    echo "Next backup in $BACKUP_INTERVAL seconds"
    sleep "$BACKUP_INTERVAL"
done