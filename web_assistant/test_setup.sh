#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "Testing Web Assistant Setup..."

# Check Docker installation
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker is installed${NC}"

# Check Docker Compose installation
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Docker Compose is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose is installed${NC}"

# Check X11
if ! command -v xhost &> /dev/null; then
    echo -e "${RED}X11 is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ X11 is installed${NC}"

# Create data directory and files
mkdir -p data
touch data/sources.txt data/networks.txt data/collector.json data/analyzer.json
echo -e "${GREEN}✓ Data directory and files created${NC}"

# Test Docker build
echo "Building Docker image..."
if ! docker-compose build --no-cache; then
    echo -e "${RED}Docker build failed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker build successful${NC}"

# Test X11 permissions
echo "Setting X11 permissions..."
xhost +local:docker
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to set X11 permissions${NC}"
    exit 1
fi
echo -e "${GREEN}✓ X11 permissions set${NC}"

# Create test files
echo "Creating test files..."

# Example networks
cat > data/networks.txt << EOL
127.0.0.1:8080:user:pass
net.example.com:8080:user:pass
EOL

# Example sources
cat > data/sources.txt << EOL
https://example.com/media1
https://example.com/media2
https://example.com/content1
EOL

# Example collector config
cat > data/gallery_selectors.json << EOL
{
    "elements": [
        {
            "css_selector": "img.gallery-image",
            "xpath_selector": "//img[@class='gallery-image']",
            "element_type": "img",
            "attributes": ["src", "alt"]
        }
    ],
    "pagination": {
        "next_button": {
            "css_selector": "a.next-page",
            "element_type": "a"
        }
    }
}
EOL

# Example data selectors
cat > data/data_selectors.json << EOL
{
    "elements": [
        {
            "css_selector": "h1.title",
            "element_type": "text",
            "name": "title"
        },
        {
            "css_selector": "div.content p",
            "element_type": "text",
            "name": "description"
        }
    ],
    "pagination": {
        "url_pattern": "page/{page}"
    }
}
EOL

echo -e "${GREEN}✓ Test files created${NC}"

echo -e "\n${GREEN}Setup test completed successfully!${NC}"
echo "
Next steps:

1. For image scraping:
   docker-compose run --rm scraper gallery

2. For data scraping:
   docker-compose run --rm scraper data

3. For interactive selection:
   docker-compose run --rm scraper interactive

Configuration files:
- Proxies: data/proxies.txt
- URLs: data/urls.txt
- Gallery selectors: data/gallery_selectors.json
- Data selectors: data/data_selectors.json

For more information, see README.md"
