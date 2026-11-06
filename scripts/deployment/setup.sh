#!/bin/bash
# WorkTrack Pro - Quick Setup Script

echo "🚀 WorkTrack Pro Setup"
echo "====================="

# Check Python version
echo "✓ Checking Python version..."
python3 --version

# Create virtual environment
echo "✓ Creating virtual environment..."
python3 -m venv venv || (echo "Note: virtualenv creation failed, trying with pip..." && pip install --user virtualenv && virtualenv venv)

# Activate virtual environment
echo "✓ Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "✓ Installing dependencies..."
pip install -q -r requirements.txt

# Create .env file if not exists
if [ ! -f .env ]; then
    echo "✓ Creating .env from template..."
    cp .env.example .env
    echo "⚠️  Please update .env with your database credentials"
fi

# Run migrations
echo "✓ Running migrations..."
python manage.py migrate

# Create superuser
echo ""
echo "✓ Create superuser account:"
python manage.py createsuperuser

# Collect static files
echo "✓ Collecting static files..."
python manage.py collectstatic --noinput

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the server, run:"
echo "  source venv/bin/activate"
echo "  python manage.py runserver"
echo ""
echo "Access admin at: http://localhost:8000/admin"
echo "API documentation at: http://localhost:8000/api/"
