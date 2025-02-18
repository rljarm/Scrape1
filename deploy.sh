#!/bin/bash

# Exit on error
set -e

# Function to print colored output
print_message() {
    GREEN='\033[0;32m'
    NC='\033[0m'
    echo -e "${GREEN}$1${NC}"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check required commands
print_message "Checking required commands..."
REQUIRED_COMMANDS="docker docker-compose git"
for cmd in $REQUIRED_COMMANDS; do
    if ! command_exists "$cmd"; then
        echo "Error: $cmd is required but not installed."
        exit 1
    fi
done

# Check if .env file exists
if [ ! -f .env ]; then
    print_message "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env file with your configuration"
    exit 1
fi

# Create required directories
print_message "Creating required directories..."
mkdir -p \
    nginx \
    certbot/conf \
    certbot/www \
    web_assistant/backend/media \
    web_assistant/backend/staticfiles

# Pull latest changes
print_message "Pulling latest changes..."
git pull origin main

# Build and start containers
print_message "Building and starting containers..."
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Initialize SSL certificate
print_message "Initializing SSL certificate..."
domain=$(grep DOMAIN_NAME .env | cut -d '=' -f2)
email=$(grep CERTBOT_EMAIL .env | cut -d '=' -f2)

if [ ! -d "certbot/conf/live/$domain" ]; then
    print_message "Obtaining SSL certificate for $domain..."
    docker-compose -f docker-compose.prod.yml run --rm certbot \
        certbot certonly --webroot \
        --webroot-path=/var/www/certbot \
        --email $email \
        --agree-tos \
        --no-eff-email \
        -d $domain \
        -d www.$domain
fi

# Reload nginx to apply SSL configuration
print_message "Reloading nginx configuration..."
docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload

# Apply database migrations
print_message "Applying database migrations..."
docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate

# Collect static files
print_message "Collecting static files..."
docker-compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput

# Create cache tables
print_message "Creating cache tables..."
docker-compose -f docker-compose.prod.yml exec backend python manage.py createcachetable

# Check services health
print_message "Checking service health..."
docker-compose -f docker-compose.prod.yml ps

# Print success message
print_message "Deployment completed successfully!"
print_message "Your application is now running at https://$domain"

# Print logs
print_message "Recent logs:"
docker-compose -f docker-compose.prod.yml logs --tail=50

# Print helpful commands
print_message "Helpful commands:"
echo "- View logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "- Restart services: docker-compose -f docker-compose.prod.yml restart"
echo "- Stop services: docker-compose -f docker-compose.prod.yml down"
echo "- Update deployment: ./deploy.sh"
