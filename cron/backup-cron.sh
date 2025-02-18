#!/bin/bash

# Set working directory to project root
PROJECT_DIR="$(dirname "$(dirname "$(readlink -f "$0")")")"
cd "$PROJECT_DIR"

# Load environment variables
if [ -f .env ]; then
    source .env
else
    echo "Error: .env file not found"
    exit 1
fi

# Function to send notification
send_notification() {
    local status=$1
    local message=$2
    
    # Slack notification (if configured)
    if [ ! -z "$SLACK_WEBHOOK_URL" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"[$status] Backup: $message\"}" \
            "$SLACK_WEBHOOK_URL"
    fi
    
    # Email notification (if configured)
    if [ ! -z "$ADMIN_EMAIL" ]; then
        echo "[$status] Backup: $message" | mail -s "Backup $status" "$ADMIN_EMAIL"
    fi
}

# Create log directory
mkdir -p logs

# Run backup with logging
LOGFILE="logs/backup_$(date +%Y%m%d_%H%M%S).log"
if ./backup.sh > "$LOGFILE" 2>&1; then
    # Backup successful
    BACKUP_SIZE=$(tail -n 2 "$LOGFILE" | grep "Backup size:" | cut -d: -f2 | tr -d ' ')
    send_notification "SUCCESS" "Backup completed successfully. Size: $BACKUP_SIZE"
    
    # Cleanup old logs
    find logs -name "backup_*.log" -mtime +7 -delete
else
    # Backup failed
    ERROR_MESSAGE=$(tail -n 5 "$LOGFILE")
    send_notification "FAILURE" "Backup failed. Last 5 lines of log:\n$ERROR_MESSAGE"
    
    # Exit with error
    exit 1
fi

# Check disk space
DISK_USAGE=$(df -h "$BACKUP_DIR" | awk 'NR==2 {print $5}' | tr -d '%')
if [ "$DISK_USAGE" -gt 80 ]; then
    send_notification "WARNING" "Backup directory disk usage is at ${DISK_USAGE}%"
fi

# Check database size
DB_SIZE=$(docker-compose -f docker-compose.prod.yml exec -T db psql -U "$DB_USER" -d "$DB_NAME" -c "SELECT pg_size_pretty(pg_database_size('$DB_NAME'));" | awk 'NR==3')
send_notification "INFO" "Current database size: $DB_SIZE"

# Optional: Check S3 backup sync
if [ ! -z "$BACKUP_S3_BUCKET" ]; then
    if ! aws s3 ls "s3://$BACKUP_S3_BUCKET/backups/" >/dev/null 2>&1; then
        send_notification "WARNING" "Unable to access S3 backup bucket"
    fi
fi

# Print completion message
echo "Backup cron job completed at $(date)"
echo "Log file: $LOGFILE"
