#!/bin/bash

# LinkedIn Recruiter Swarm - Quick Start Script
# This script automates the setup process

set -e  # Exit on error

echo "================================================================================"
echo "  LinkedIn Recruiter Swarm - Quick Start"
echo "================================================================================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

echo -e "${GREEN}✓ Docker found${NC}"

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed${NC}"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo -e "${GREEN}✓ Docker Compose found${NC}"

# Function to use docker compose (v2) or docker-compose (v1)
docker_compose() {
    if command -v docker-compose &> /dev/null; then
        docker-compose "$@"
    else
        docker compose "$@"
    fi
}

echo ""
echo "Step 1: Starting Neo4j with Docker Compose..."
echo "--------------------------------------------------------------------------------"

# Start Neo4j
docker_compose up -d

echo -e "${GREEN}✓ Neo4j container started${NC}"

# Wait for Neo4j to be ready
echo ""
echo "Waiting for Neo4j to start (this may take 30-60 seconds)..."
for i in {1..30}; do
    if docker exec neo4j-recruiter cypher-shell -u neo4j -p recruiter123 "RETURN 1" &>/dev/null; then
        echo -e "${GREEN}✓ Neo4j is ready!${NC}"
        break
    fi
    echo -n "."
    sleep 2
done

echo ""
echo "Step 2: Setting up Python environment..."
echo "--------------------------------------------------------------------------------"

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✓ Python ${PYTHON_VERSION} found${NC}"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip > /dev/null
pip install -r requirements.txt > /dev/null 2>&1
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Copy .env.example to .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo -e "${GREEN}✓ .env file created${NC}"
else
    echo -e "${YELLOW}.env file already exists${NC}"
fi

echo ""
echo "Step 3: Testing Neo4j connection..."
echo "--------------------------------------------------------------------------------"

python test_neo4j.py

echo ""
echo "Step 4: Setting up database schema and sample data..."
echo "--------------------------------------------------------------------------------"

python setup_neo4j.py --sample-data

echo ""
echo "================================================================================"
echo "  ✓ Quick Start Complete!"
echo "================================================================================"

echo ""
echo "Next steps:"
echo "  1. Run the demo:"
echo "     ${GREEN}python main.py${NC}"
echo ""
echo "  2. Access Neo4j Browser:"
echo "     ${GREEN}http://localhost:7474${NC}"
echo "     Username: neo4j"
echo "     Password: recruiter123"
echo ""
echo "  3. View documentation:"
echo "     ${GREEN}cat README.md${NC}"
echo ""
echo "  4. Stop Neo4j when done:"
echo "     ${GREEN}docker-compose down${NC}"
echo ""
echo "Happy recruiting! 🚀"
echo ""
