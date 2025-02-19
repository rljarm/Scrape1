# Web Assistant

A Progressive Web Application (PWA) Web Crawler with React frontend and Django backend that provides advanced web scraping capabilities, AI-powered controls, and comprehensive data extraction features.

## Features

### Core Crawling & Data Extraction
- **Proxy Management**
  - Multiple input methods (textbox, file upload)
  - Six rotation strategies (random, round-robin, percentage based, sticky session, custom rules)
  - Real-time failover and assignment
- **Concurrency Management**
  - Manual and auto-scalable concurrency settings
  - Real-time performance recommendations
- **Real-Time Progress Tracking**
  - Live updates via Django Channels/WebSockets
  - Interactive dashboard with progress bars and logs
- **Resumable Crawling**
  - Persistent storage of URL crawl status
  - Automatic state saving at page and post-download levels
- **Dynamic Content Extraction**
  - Playwright integration for rendered DOM capture
  - Live preview for interactive element selection
- **Interactive Data Selection**
  - Single-element and batch selection modes
  - Element vs HTML block selection toggle
  - Extended attribute support
  - Multi-element pattern recognition
- **Advanced Pagination**
  - Standard pagination support
  - Infinite scroll detection
  - Custom selector configuration

### Authentication & Management
- **Login & Session Management**
  - Credential management for authenticated crawling
  - Cookie/token handling
  - Failed login notifications
- **Robots.txt & Sitemap Support**
  - Automatic detection and adherence
  - Crawl scheduling and rate limiting
- **Error Handling**
  - Automated retries
  - Comprehensive logging
  - User notifications

### AI Integration
- **LangChain/LangGraph Integration**
  - Customizable AI workflows
  - Natural language query capabilities
- **Search API Integration**
  - Bing, Google, Brave Search API support
  - AI-driven content recommendations
- **YouTube Integration**
  - Video content extraction
  - Metadata processing
  - Transcript extraction
- **Content Processing**
  - Dynamic content classification
  - NLP-based summarization
  - Keyword extraction
  - Optional visual recognition

## Project Structure

```
web_assistant/
├── frontend/                # React PWA frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── hooks/         # Custom React hooks
│   │   └── services/      # API services
│   └── public/            # Static assets
├── backend/                # Django backend
│   ├── crawling/          # Crawling logic
│   │   ├── proxy/        # Proxy management
│   │   ├── extractors/   # Data extractors
│   │   └── schedulers/   # Crawl schedulers
│   ├── ai/               # AI integrations
│   │   ├── langchain/    # LangChain integration
│   │   └── search/       # Search API integration
│   └── api/              # REST API endpoints
└── docker/                # Docker configuration
```

## Installation

1. Clone the repository

2. Frontend setup:
```bash
cd frontend
npm install
npm start
```

3. Backend setup:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

4. Using Docker:
```bash
docker-compose up --build
```

## Configuration

Key settings to configure:

- Proxy rotation strategies
- Concurrency limits
- AI model settings
- API keys for search integrations
- Rate limiting parameters
- Database settings

## Usage

1. Access the web interface at `http://localhost:3000`

2. Configure crawling settings:
   - Add target URLs
   - Set proxy configuration
   - Configure extraction rules
   - Set up AI processing options

3. Monitor and manage crawls:
   - View real-time progress
   - Manage active crawls
   - Export collected data
   - View AI insights

## Development

### Prerequisites
- Node.js 16+
- Python 3.8+
- Docker (optional)

### Running Tests
```bash
# Frontend tests
cd frontend
npm test

# Backend tests
cd backend
python manage.py test
```

### Building for Production
```bash
# Frontend build
cd frontend
npm run build

# Docker build
docker-compose -f docker-compose.prod.yml up --build
```

## Deployment

### Initial Setup
1. Clone the repository
2. Copy `.env.example` to `.env` and configure environment variables
3. Run the deployment script:
```bash
chmod +x deploy.sh
./deploy.sh
```

### SSL Configuration
The deployment includes automatic SSL certificate management with Let's Encrypt:
1. Configure your domain in `.env`
2. The system will automatically obtain and renew SSL certificates
3. Certificates are stored in `certbot/conf/`

### Backup System
Automated backup system for database and media files:
```bash
# Manual backup
./backup.sh

# Configure automated backups
crontab cron/crontab.conf
```

Backup features:
- Daily automated backups
- Configurable retention period
- Optional S3 backup sync
- Backup verification
- Email/Slack notifications

### Monitoring
System monitoring with alerts:
```bash
# Manual monitoring check
./cron/monitor.sh

# View monitoring logs
tail -f logs/monitor_*.log
```

Monitoring features:
- Service health checks
- Resource usage monitoring
- SSL certificate expiry checks
- Error log analysis
- Automated notifications

### Log Management
Automated log rotation and management:
- Application logs in `logs/`
- Docker container logs
- Nginx access/error logs
- Database logs
- Configurable retention periods

### Maintenance Tasks
Regular maintenance is automated through cron jobs:
- Database vacuuming
- Docker image updates
- System pruning
- SSL certificate renewal
- Log rotation

### Scaling
To scale the application:
1. Adjust resource limits in `docker-compose.prod.yml`
2. Modify the number of Celery workers
3. Configure load balancing in nginx
4. Scale services:
```bash
docker-compose -f docker-compose.prod.yml up -d --scale celery=3
```

### Troubleshooting
Common issues and solutions:
1. Service not starting:
   ```bash
   docker-compose -f docker-compose.prod.yml logs [service_name]
   ```

2. Database connection issues:
   ```bash
   docker-compose -f docker-compose.prod.yml exec db pg_isready
   ```

3. Redis connection issues:
   ```bash
   docker-compose -f docker-compose.prod.yml exec redis redis-cli ping
   ```

4. SSL certificate issues:
   ```bash
   docker-compose -f docker-compose.prod.yml exec certbot certbot certificates
   ```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[License information here]
