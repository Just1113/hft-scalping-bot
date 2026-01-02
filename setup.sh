#!/bin/bash

# ============================================
# High Frequency Scalping Bot Setup Script
# ============================================

set -e  # Exit on error

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║    🤖 High Frequency Scalping Bot Setup                  ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Check Python version
echo "🔍 Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || [ "$PYTHON_MINOR" -lt 9 ]; then
    echo "❌ Python 3.9 or higher is required. Found Python $PYTHON_VERSION"
    exit 1
fi
echo "✅ Python $PYTHON_VERSION detected"

# Create virtual environment
echo ""
echo "📦 Setting up virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "⚠️  Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "📥 Installing dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "✅ Dependencies installed"
else
    echo "❌ requirements.txt not found!"
    exit 1
fi

# Create necessary directories
echo ""
echo "📁 Creating directory structure..."
mkdir -p logs models data static
echo "✅ Directories created:"
echo "   - logs/    (for log files)"
echo "   - models/  (for ML models)"
echo "   - data/    (for database)"
echo "   - static/  (for static files)"

# Copy environment file
echo ""
echo "⚙️  Setting up configuration..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ Created .env file from template"
        echo ""
        echo "⚠️  IMPORTANT: Edit the .env file with your API keys!"
        echo "   Required changes:"
        echo "   1. BYBIT_API_KEY and BYBIT_API_SECRET"
        echo "   2. TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID"
        echo ""
    else
        echo "❌ .env.example not found!"
        exit 1
    fi
else
    echo "⚠️  .env file already exists (skipping)"
fi

# Create database
echo ""
echo "🗄️  Initializing database..."
if [ -f "app/database.py" ]; then
    python -c "
import asyncio
from app.database import init_db
asyncio.run(init_db())
print('✅ Database initialized')
"
else
    echo "⚠️  Could not initialize database (app/database.py not found)"
fi

# Test imports
echo ""
echo "🧪 Testing imports..."
python -c "
try:
    import pandas
    import numpy
    from pybit.unified_trading import HTTP
    from telegram.ext import Application
    print('✅ All imports successful')
except ImportError as e:
    print(f'❌ Import error: {e}')
    exit(1)
"

# Create test configuration
echo ""
echo "🔧 Creating test configuration..."
cat > test_config.py << 'EOF'
from app.config import TradingConfig

config = TradingConfig.from_env()
if config.validate():
    print("✅ Configuration is valid")
else:
    print("❌ Configuration is invalid")
    print("Please check your .env file")
EOF

python test_config.py
rm test_config.py

# Create basic log file
echo ""
echo "📝 Setting up logging..."
LOGFILE="logs/setup_$(date +%Y%m%d_%H%M%S).log"
echo "Setup completed at $(date)" > $LOGFILE
echo "Python: $PYTHON_VERSION" >> $LOGFILE

# Final instructions
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                    SETUP COMPLETE!                       ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "🎉 High Frequency Scalping Bot is ready!"
echo ""
echo "📋 Next steps:"
echo ""
echo "1. EDIT CONFIGURATION:"
echo "   nano .env  # or use your favorite editor"
echo "   • Add your Bybit API keys (start with TESTNET!)"
echo "   • Add your Telegram bot token and chat ID"
echo ""
echo "2. TEST LOCALLY:"
echo "   source venv/bin/activate"
echo "   python app/main.py"
echo ""
echo "3. DEPLOY TO RENDER:"
echo "   git add ."
echo "   git commit -m 'Initial commit: HFT Scalping Bot'"
echo "   git push origin main"
echo "   • Go to https://render.com"
echo "   • Connect your repository"
echo "   • Deploy with Docker"
echo ""
echo "4. MONITOR:"
echo "   • Check logs: tail -f logs/*.log"
echo "   • Use Telegram commands: /start, /status"
echo ""
echo "⚠️  IMPORTANT SAFETY NOTES:"
echo "   • ALWAYS start with TESTNET (BYBIT_TESTNET=true)"
echo "   • Use small position sizes initially"
echo "   • Monitor bot performance regularly"
echo "   • Never risk more than you can afford to lose"
echo ""
echo "📞 Need help? Check the README.md file"
echo ""
