#!/bin/bash

# HiyaDrive Development Environment Setup
# Usage: bash setup_dev.sh

set -e  # Exit on error

echo "=============================================="
echo "HiyaDrive Development Environment Setup"
echo "=============================================="
echo ""

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo -e "${BLUE}1. Checking Python version...${NC}"
python3 --version
python3_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python3_version" | sort -V | head -n1)" = "$required_version" ]; then
    echo -e "${GREEN}✓ Python $python3_version is compatible${NC}"
else
    echo -e "${YELLOW}⚠ Warning: Python $python3_version may not be fully compatible (requires 3.9+)${NC}"
fi
echo ""

# Create virtual environment
echo -e "${BLUE}2. Creating virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}⚠ Virtual environment already exists${NC}"
fi
echo ""

# Activate virtual environment
echo -e "${BLUE}3. Activating virtual environment...${NC}"
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo ""

# Upgrade pip
echo -e "${BLUE}4. Upgrading pip...${NC}"
pip install --upgrade pip setuptools wheel > /dev/null 2>&1
echo -e "${GREEN}✓ pip upgraded${NC}"
echo ""

# Install dependencies
echo -e "${BLUE}5. Installing dependencies...${NC}"
pip install -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Install dev dependencies
echo -e "${BLUE}6. Installing development dependencies...${NC}"
pip install pytest pytest-asyncio pytest-cov pytest-mock black pylint mypy ipython
echo -e "${GREEN}✓ Development dependencies installed${NC}"
echo ""

# Create directories
echo -e "${BLUE}7. Creating necessary directories...${NC}"
mkdir -p data/logs data/recordings config
echo -e "${GREEN}✓ Directories created${NC}"
echo ""

# Create .env if not exists
echo -e "${BLUE}8. Checking environment configuration...${NC}"
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env file (using defaults)${NC}"
else
    echo -e "${YELLOW}⚠ .env file already exists${NC}"
fi
echo ""

# Test imports
echo -e "${BLUE}9. Testing Python imports...${NC}"
python3 -c "
import hiya_drive
from hiya_drive.config.settings import settings
from hiya_drive.core.orchestrator import BookingOrchestrator
from hiya_drive.voice.voice_processor import VoiceProcessor
print('✓ All imports successful')
"
echo ""

# Show next steps
echo -e "${GREEN}=============================================="
echo "✓ Setup Complete!"
echo "===============================================${NC}"
echo ""
echo "Next steps:"
echo ""
echo "1. Activate the virtual environment:"
echo -e "   ${BLUE}source venv/bin/activate${NC}"
echo ""
echo "2. Run a demo:"
echo -e "   ${BLUE}python -m hiya_drive.main demo${NC}"
echo ""
echo "3. Run tests:"
echo -e "   ${BLUE}pytest tests/ -v${NC}"
echo ""
echo "4. View system status:"
echo -e "   ${BLUE}python -m hiya_drive.main status${NC}"
echo ""
echo "5. Test microphone:"
echo -e "   ${BLUE}python -m hiya_drive.main test-audio${NC}"
echo ""
echo "For more commands, see the Makefile:"
echo -e "   ${BLUE}make help${NC}"
echo ""
