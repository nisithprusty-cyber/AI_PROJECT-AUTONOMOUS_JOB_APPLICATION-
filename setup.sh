#!/bin/bash
# ================================================
# ApplyGenius — Setup Script
# Run this once to install all dependencies
# ================================================

set -e

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   ApplyGenius — Autonomous Job Agent     ║"
echo "║          Setup & Installation            ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required. Install from https://python.org"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate
source venv/bin/activate

echo "📦 Installing Python dependencies..."
pip install --upgrade pip -q
pip install -r backend/requirements.txt

# Create .env from template if not exists
if [ ! -f "backend/.env" ]; then
    echo ""
    echo "⚙️  Creating .env file from template..."
    cp backend/.env.example backend/.env
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📝 IMPORTANT: Edit backend/.env and add:"
    echo "   1. NVIDIA_API_KEY  → https://build.nvidia.com"
    echo "   2. GOOGLE_SHEETS_ID → Your Google Sheet ID"
    echo "   3. GOOGLE_CREDENTIALS_FILE → credentials.json path"
    echo "   4. EMAIL_SENDER + EMAIL_APP_PASSWORD (optional)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
fi

# Create required directories
mkdir -p backend/uploads
mkdir -p backend/outputs

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit backend/.env with your API keys"
echo "  2. Run: bash run.sh"
echo ""
