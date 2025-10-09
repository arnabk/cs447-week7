#!/bin/bash

# News Article Clustering and Summarization - Project Setup Script
# This script sets up the entire project environment

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on macOS or Linux
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
else
    print_error "Unsupported operating system: $OSTYPE"
    exit 1
fi

print_status "Starting project setup for $OS..."

# Check if Python 3.8+ is installed
print_status "Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    print_success "Python $PYTHON_VERSION found"
    
    # Check if version is 3.8 or higher
    if python3 -c 'import sys; exit(0 if sys.version_info >= (3, 8) else 1)'; then
        print_success "Python version is compatible (3.8+)"
    else
        print_error "Python 3.8 or higher is required. Found: $PYTHON_VERSION"
        exit 1
    fi
else
    print_error "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 is not installed. Please install pip."
    exit 1
fi

print_success "pip3 found"

# Create virtual environment
print_status "Creating virtual environment..."
if [ -d "venv" ]; then
    print_warning "Virtual environment already exists. Removing old one..."
    rm -rf venv
fi

python3 -m venv venv
print_success "Virtual environment created"

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate
print_success "Virtual environment activated"

# Upgrade pip
print_status "Upgrading pip..."
source venv/bin/activate && pip install --upgrade pip
print_success "pip upgraded"

# Install system dependencies (if needed)
print_status "Installing system dependencies..."

if [[ "$OS" == "macos" ]]; then
    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        print_warning "Homebrew not found. Some dependencies might need manual installation."
    else
        print_status "Installing system dependencies via Homebrew..."
        # Install PostgreSQL if not present
        if ! brew list postgresql &> /dev/null; then
            print_status "Installing PostgreSQL..."
            brew install postgresql
        fi
        # Install Redis if not present
        if ! brew list redis &> /dev/null; then
            print_status "Installing Redis..."
            brew install redis
        fi
    fi
elif [[ "$OS" == "linux" ]]; then
    print_status "Installing system dependencies via apt..."
    # Update package list
    sudo apt-get update
    
    # Install PostgreSQL
    if ! dpkg -l | grep -q postgresql; then
        print_status "Installing PostgreSQL..."
        sudo apt-get install -y postgresql postgresql-contrib
    fi
    
    # Install Redis
    if ! dpkg -l | grep -q redis; then
        print_status "Installing Redis..."
        sudo apt-get install -y redis-server
    fi
    
    # Install build essentials for Python packages
    sudo apt-get install -y build-essential python3-dev
fi

# Install Python dependencies
print_status "Installing Python dependencies..."
source venv/bin/activate && pip install -r requirements.txt
print_success "Python dependencies installed"

# Download NLTK data
print_status "Downloading NLTK data..."
source venv/bin/activate && python -c "
import nltk
try:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')
    nltk.download('averaged_perceptron_tagger')
    print('NLTK data downloaded successfully')
except Exception as e:
    print(f'Warning: Could not download NLTK data: {e}')
"

# Download spaCy model
print_status "Downloading spaCy English model..."
source venv/bin/activate && python -m spacy download en_core_web_sm

# Create necessary directories
print_status "Creating project directories..."
mkdir -p data
mkdir -p models
mkdir -p logs
mkdir -p tmp
print_success "Project directories created"

# Create .env file from example
if [ -f "env.example" ] && [ ! -f ".env" ]; then
    print_status "Creating .env file from example..."
    cp env.example .env
    print_success ".env file created"
    print_warning "Please update .env file with your configuration"
else
    print_warning ".env file already exists or env.example not found"
fi

# Note: Database setup removed as this is a research project using Jupyter notebooks
print_status "Skipping database setup (research project uses Jupyter notebooks)"

# Run basic tests to verify installation
print_status "Running basic tests..."
source venv/bin/activate && python -c "
try:
    import numpy as np
    import pandas as pd
    import sklearn
    import spacy
    import transformers
    import torch
    import hdbscan
    import umap
    import feedparser
    import jupyter
    print('All core dependencies imported successfully')
except ImportError as e:
    print(f'Warning: Some dependencies might not be properly installed: {e}')
"

# Make the script executable
chmod +x setup.sh

print_success "Project setup completed successfully!"
print_status "Next steps:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Update the .env file with your configuration"
echo "3. Start Jupyter notebooks: jupyter lab"
echo "4. Or use Docker: docker-compose up"
echo ""
print_status "For Docker setup, run: docker-compose up --build"
print_status "For development, activate venv and run: jupyter lab"
