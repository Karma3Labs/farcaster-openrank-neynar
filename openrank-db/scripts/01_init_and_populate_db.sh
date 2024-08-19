#!/bin/bash
# Download and import the initial database schema and data
set -e

FLAG_FILE="/tmp/initialized.flag"

if [ -f "$FLAG_FILE" ]; then
    echo "Initialization already completed. Exiting..."
    exit 0
fi

export PGPASSWORD=${POSTGRES_PASSWORD}

set -x
set -e  # Exit immediately if a command exits with a non-zero status
set -o pipefail  # Ensure pipeline failures are propagated

# S3 details
S3_BUCKET=$S3_BUCKET
S3_PREFIX=$S3_PREFIX # e.g., "database-backups/"
BACKUP_FILE="backup.tar.gz"

# Local backup details
BACKUP_DIR="/tmp/backup"

# Target database details
TARGET_DB_HOST=$POSTGRES_HOST
TARGET_DB_PORT=$POSTGRES_PORT
TARGET_DB_NAME=$POSTGRES_NAME
TARGET_DB_USER=$POSTGRES_USER
# Function to clean up temporary files
cleanup() {
    echo "Cleaning up..."
    rm -rf "$BACKUP_DIR"
    unset PGPASSWORD
}

# Set up trap to ensure cleanup happens even if script is interrupted
trap cleanup EXIT INT TERM

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Download backup from S3
echo "Downloading backup from S3..."
aws s3 cp "s3://$S3_BUCKET/$S3_PREFIX$BACKUP_FILE" "$BACKUP_DIR/$BACKUP_FILE"

if [ $? -ne 0 ]; then
    echo "Failed to download backup from S3"
    exit 1
fi

# Decompress the backup
echo "Decompressing backup..."
tar xzf "$BACKUP_DIR/$BACKUP_FILE" -C "$BACKUP_DIR"

# Restore the database
echo "Restoring database..."
set +x  # Disable command echoing
export PGPASSWORD="$TARGET_DB_PASSWORD"
set -x  # Re-enable command echoing

# First, drop the database if it exists and create a new one
psql -h "$TARGET_DB_HOST" -p "$TARGET_DB_PORT" -U "$TARGET_DB_USER" -d postgres -c "DROP DATABASE IF EXISTS $TARGET_DB_NAME;"
psql -h "$TARGET_DB_HOST" -p "$TARGET_DB_PORT" -U "$TARGET_DB_USER" -d postgres -c "CREATE DATABASE $TARGET_DB_NAME;"

# Now restore the data
pg_restore -h "$TARGET_DB_HOST" -p "$TARGET_DB_PORT" -U "$TARGET_DB_USER" -d "$TARGET_DB_NAME" -j 4 --no-owner --no-acl "$BACKUP_DIR/backup"

unset PGPASSWORD

if [ $? -eq 0 ]; then
    echo "Database restored successfully"
else
    echo "Failed to restore database"
    exit 1
fi

# Cleanup function will be called automatically here to remove temporary files
