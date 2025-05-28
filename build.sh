#!/bin/bash

# Exit on any error
set -e

echo "🚀 Starting Render build process..."

# Update pip and install dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput --clear

# Run database migrations
echo "🗄️ Running database migrations..."
python manage.py migrate --noinput

# Create superuser if it doesn't exist (optional)
# Uncomment the following lines if you want to create a default superuser
# echo "👤 Creating superuser..."
# python manage.py shell -c "
# from django.contrib.auth import get_user_model;
# User = get_user_model();
# if not User.objects.filter(username='admin').exists():
#     User.objects.create_superuser('admin', 'admin@example.com', 'your-secure-password')
# "

echo "✅ Build process completed successfully!" 