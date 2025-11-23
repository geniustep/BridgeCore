#!/bin/bash
# Script to install dependencies for BridgeCore project
# This script sets up a virtual environment and installs all required packages

set -e  # Exit on error

echo "🚀 BridgeCore - Dependency Installation Script"
echo "=============================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Python version
echo "📋 Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Python version: $PYTHON_VERSION"

# Check if Python 3.11+ is available
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
if [ "$PYTHON_MINOR" -lt 11 ]; then
    echo -e "${RED}❌ Error: Python 3.11+ is required. Found: $PYTHON_VERSION${NC}"
    exit 1
fi

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo ""
echo "📁 Project directory: $PROJECT_DIR"
echo ""

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment already exists${NC}"
    read -p "Do you want to recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️  Removing existing virtual environment..."
        rm -rf venv
    else
        echo "✅ Using existing virtual environment"
        source venv/bin/activate
        SKIP_VENV=true
    fi
fi

# Create virtual environment if needed
if [ ! "$SKIP_VENV" = true ]; then
    echo "🔧 Creating virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "📦 Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install requirements
echo ""
echo "📥 Installing production dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo -e "${GREEN}✅ Production dependencies installed${NC}"
else
    echo -e "${RED}❌ Error: requirements.txt not found${NC}"
    exit 1
fi

# Install development dependencies (optional)
if [ -f "requirements-dev.txt" ]; then
    echo ""
    read -p "Do you want to install development dependencies? (Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        echo "📥 Installing development dependencies..."
        pip install -r requirements-dev.txt
        echo -e "${GREEN}✅ Development dependencies installed${NC}"
    fi
fi

# Verify installation
echo ""
echo "🔍 Verifying installation..."
python3 -c "import fastapi; print(f'✅ FastAPI {fastapi.__version__}')" || echo -e "${RED}❌ FastAPI not installed${NC}"
python3 -c "import httpx; print(f'✅ httpx {httpx.__version__}')" || echo -e "${RED}❌ httpx not installed${NC}"
python3 -c "import pydantic; print(f'✅ Pydantic {pydantic.__version__}')" || echo -e "${RED}❌ Pydantic not installed${NC}"

# Check for pytest if dev dependencies installed
if python3 -c "import pytest" 2>/dev/null; then
    pytest_version=$(python3 -c "import pytest; print(pytest.__version__)")
    echo -e "${GREEN}✅ pytest $pytest_version${NC}"
fi

echo ""
echo -e "${GREEN}✨ Installation complete!${NC}"
echo ""
echo "📝 Next steps:"
echo "   1. Activate virtual environment: source venv/bin/activate"
echo "   2. Set up environment variables: cp .env.example .env"
echo "   3. Edit .env with your configuration"
echo "   4. Run database migrations: alembic upgrade head"
echo "   5. Run tests: pytest"
echo "   6. Start server: uvicorn app.main:app --reload"
echo ""

