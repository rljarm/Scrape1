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
            --data "{\"text\":\"[$status] Monitor: $message\"}" \
            "$SLACK_WEBHOOK_URL"
    fi
    
    # Email notification (if configured)
    if [ ! -z "$ADMIN_EMAIL" ]; then
        echo "[$status] Monitor: $message" | mail -s "Monitor $status" "$ADMIN_EMAIL"
    fi
}

# Create log directory
mkdir -p logs

# Log file
LOGFILE="logs/monitor_$(date +%Y%m%d_%H%M%S).log"
exec 1> >(tee -a "$LOGFILE")
exec 2>&1

echo "Starting system monitoring at $(date)"

# Check Docker containers
echo "Checking Docker containers..."
CONTAINERS=(frontend backend celery celery-beat nginx redis db)
for container in "${CONTAINERS[@]}"; do
    if ! docker-compose -f docker-compose.prod.yml ps "$container" | grep -q "Up"; then
        send_notification "ALERT" "Container $container is not running"
    fi
done

# Check service health
echo "Checking service health..."

# Frontend health check
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000)
if [ "$FRONTEND_STATUS" != "200" ]; then
    send_notification "ALERT" "Frontend service is not responding (Status: $FRONTEND_STATUS)"
fi

# Backend health check
BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/health/)
if [ "$BACKEND_STATUS" != "200" ]; then
    send_notification "ALERT" "Backend service is not responding (Status: $BACKEND_STATUS)"
fi

# Check Redis
echo "Checking Redis connection..."
if ! docker-compose -f docker-compose.prod.yml exec -T redis redis-cli ping | grep -q "PONG"; then
    send_notification "ALERT" "Redis is not responding"
fi

# Check PostgreSQL
echo "Checking PostgreSQL connection..."
if ! docker-compose -f docker-compose.prod.yml exec -T db pg_isready -U "$DB_USER" | grep -q "accepting connections"; then
    send_notification "ALERT" "PostgreSQL is not responding"
fi

# Check system resources
echo "Checking system resources..."

# CPU usage
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d. -f1)
if [ "$CPU_USAGE" -gt 80 ]; then
    send_notification "WARNING" "High CPU usage: ${CPU_USAGE}%"
fi

# Memory usage
MEMORY_USAGE=$(free | grep Mem | awk '{print int($3/$2 * 100)}')
if [ "$MEMORY_USAGE" -gt 80 ]; then
    send_notification "WARNING" "High memory usage: ${MEMORY_USAGE}%"
fi

# Disk usage
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | tr -d '%')
if [ "$DISK_USAGE" -gt 80 ]; then
    send_notification "WARNING" "High disk usage: ${DISK_USAGE}%"
fi

# Check SSL certificate expiry
echo "Checking SSL certificate..."
DOMAIN=$(grep DOMAIN_NAME .env | cut -d '=' -f2)
SSL_EXPIRY=$(echo | openssl s_client -servername "$DOMAIN" -connect "$DOMAIN":443 2>/dev/null | openssl x509 -noout -enddate | cut -d= -f2)
SSL_EXPIRY_DAYS=$(( ( $(date -d "$SSL_EXPIRY" +%s) - $(date +%s) ) / 86400 ))
if [ "$SSL_EXPIRY_DAYS" -lt 30 ]; then
    send_notification "WARNING" "SSL certificate will expire in $SSL_EXPIRY_DAYS days"
fi

# Check Celery workers
echo "Checking Celery workers..."
CELERY_WORKERS=$(docker-compose -f docker-compose.prod.yml exec -T celery celery -A web_assistant inspect active)
if [ $? -ne 0 ]; then
    send_notification "ALERT" "Celery workers are not responding"
fi

# Check recent error logs
echo "Checking error logs..."
ERROR_COUNT=$(docker-compose -f docker-compose.prod.yml logs --since 1h | grep -i error | wc -l)
if [ "$ERROR_COUNT" -gt 10 ]; then
    send_notification "WARNING" "High number of errors in logs: $ERROR_COUNT in the last hour"
fi

# Check backup status
echo "Checking backup status..."
LAST_BACKUP=$(ls -t "$BACKUP_DIR" 2>/dev/null | head -n1)
if [ -z "$LAST_BACKUP" ]; then
    send_notification "WARNING" "No backups found"
else
    BACKUP_AGE=$(( ( $(date +%s) - $(date -r "$BACKUP_DIR/$LAST_BACKUP" +%s) ) / 3600 ))
    if [ "$BACKUP_AGE" -gt 24 ]; then
        send_notification "WARNING" "Last backup is over 24 hours old"
    fi
fi

# Cleanup old logs
find logs -name "monitor_*.log" -mtime +7 -delete

echo "Monitoring completed at $(date)"
echo "Log file: $LOGFILE"
