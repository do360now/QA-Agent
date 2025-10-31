#!/bin/bash
# Setup script for Autonomous Web Testing Swarm

set -e

echo "🐝 Autonomous Web Testing Swarm - Setup Script"
echo "=============================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.10"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python 3.10 or higher required. Found: $python_version"
    exit 1
fi
echo "✅ Python $python_version found"
echo ""

# Check if Ollama is installed
echo "Checking Ollama installation..."
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama not found!"
    echo ""
    echo "Please install Ollama first:"
    echo "  macOS/Linux: curl -fsSL https://ollama.com/install.sh | sh"
    echo "  Or visit: https://ollama.com/download"
    exit 1
fi
echo "✅ Ollama found"
echo ""

# Check if Ollama is running
echo "Checking if Ollama is running..."
if curl -s http://localhost:11434 > /dev/null 2>&1; then
    echo "✅ Ollama is running"
else
    echo "⚠️  Ollama is not running. Starting it..."
    echo "Please run 'ollama serve' in a separate terminal"
    echo ""
fi
echo ""

# Pull Llama model
echo "Checking for llama3.2:3b model..."
if ollama list | grep -q "llama3.2:3b"; then
    echo "✅ llama3.2:3b model already installed"
else
    echo "Downloading llama3.2:3b model (this may take a few minutes)..."
    ollama pull llama3.2:3b
    echo "✅ Model downloaded"
fi
echo ""

# Create virtual environment
echo "Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# Install dependencies
echo "Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "✅ Python dependencies installed"
echo ""

# Install Playwright browsers
echo "Installing Playwright browsers..."
playwright install chromium
echo "✅ Playwright browsers installed"
echo ""

# Create output directory
mkdir -p test-results
echo "✅ Output directory created"
echo ""

echo "=============================================="
echo "✅ Setup complete!"
echo ""
echo "To get started:"
echo "  1. Make sure Ollama is running: ollama serve"
echo "  2. Activate the virtual environment: source venv/bin/activate"
echo "  3. Run a test: python swarm_orchestrator.py --url http://localhost:3000 --num-agents 3 --duration 5"
echo ""
echo "For more options: python swarm_orchestrator.py --help"
echo "=============================================="
