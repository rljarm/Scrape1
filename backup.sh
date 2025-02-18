#!/bin/bash

# Exit on error
set -e

# Function to print colored output
print_message() {
    GREEN='\033[0;32m'
    NC='\033[0m'
    echo -e "${GREEN}$1${NC}"
}

# Load environment variables
if [ -f .env ]; then
    source .env
else
    echo "Error: .env file not found"
    exit 1
fi

# Set backup directory
BACKUP_DIR=${BACKUP_DIR:-/backups}
BACKUP_RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-7}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="$BACKUP_DIR/$TIMESTAMP"

# Create backup directories
mkdir -p "$BACKUP_PATH"/{db,media}

# Function to cleanup old backups
cleanup_old_backups() {
    print_message "Cleaning up backups older than $BACKUP_RETENTION_DAYS days..."
    find "$BACKUP_DIR" -type d -mtime +$BACKUP_RETENTION_DAYS -exec rm -rf {} \;
}

# Backup database
print_message "Backing up database..."
docker-compose -f docker-compose.prod.yml exec -T db \
    pg_dump -U $DB_USER $DB_NAME | gzip > "$BACKUP_PATH/db/database.sql.gz"

# Backup media files
print_message "Backing up media files..."
docker-compose -f docker-compose.prod.yml exec -T backend \
    tar czf - -C /app/media . > "$BACKUP_PATH/media/media_files.tar.gz"

# Create backup metadata
cat > "$BACKUP_PATH/metadata.json" << EOF
{
    "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "database": "$DB_NAME",
    "files": [
        "db/database.sql.gz",
        "media/media_files.tar.gz"
    ],
    "environment": "production"
}
EOF

# Cleanup old backups
cleanup_old_backups

# Calculate backup size
BACKUP_SIZE=$(du -sh "$BACKUP_PATH" | cut -f1)

print_message "Backup completed successfully!"
echo "Backup location: $BACKUP_PATH"
echo "Backup size: $BACKUP_SIZE"

# Restore instructions
cat << EOF

To restore this backup:

1. Database:
   gunzip -c $BACKUP_PATH/db/database.sql.gz | docker-compose -f docker-compose.prod.yml exec -T db psql -U $DB_USER $DB_NAME

2. Media files:
   docker-compose -f docker-compose.prod.yml exec -T backend rm -rf /app/media/*
   cat $BACKUP_PATH/media/media_files.tar.gz | docker-compose -f docker-compose.prod.yml exec -T backend tar xzf - -C /app/media

Note: Make sure to stop the application before restoring and restart it afterwards.
EOF

# Optional: Upload to remote storage
if [ ! -z "$BACKUP_S3_BUCKET" ]; then
    print_message "Uploading backup to S3..."
    aws s3 cp --recursive "$BACKUP_PATH" "s3://$BACKUP_S3_BUCKET/backups/$TIMESTAMP/"
fi
