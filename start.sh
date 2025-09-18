#!/bin/bash

# Kite Services Start Script
# =========================

set -e

echo "🚀 Starting Kite Services..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/upgrade dependencies
echo "📚 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️ .env file not found. Copying from .env.example..."
    if [ -f "env/env.example" ]; then
        cp env/env.example .env
        echo "📝 Please edit .env file with your actual credentials"
    else
        echo "❌ env/env.example not found. Please create .env file manually."
        exit 1
    fi
fi

# Create necessary directories
mkdir -p logs data

# Set Python path
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"

echo "✅ Setup complete!"
echo ""
echo "🎯 Starting Kite Services on port 8080..."
echo "📊 API Documentation: http://localhost:8080/docs"
echo "💊 Health Check: http://localhost:8080/health"
echo ""

# Start the service
cd src && python main.py
