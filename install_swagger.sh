#!/bin/bash

echo "Installing DevGuidance Django API with Swagger UI..."

# Activate virtual environment (if exists)
if [ -f "../bin/activate" ]; then
    echo "Activating virtual environment..."
    source ../bin/activate
fi

echo "Installing required packages..."
python -m pip install --upgrade pip
python -m pip install drf-yasg==1.21.7
python -m pip install packaging

echo "Verifying installation..."
if python -c "import drf_yasg; print('✓ drf-yasg installed successfully')" 2>/dev/null; then
    echo "✓ Installation successful"
else
    echo "✗ Failed to install drf-yasg"
    exit 1
fi

echo "Running Django migrations..."
python manage.py makemigrations
python manage.py migrate

echo "Setup complete!"
echo ""
echo "To start the server, run:"
echo "  python manage.py runserver"
echo ""
echo "Then visit:"
echo "  http://localhost:8000/swagger/     - Swagger UI"
echo "  http://localhost:8000/redoc/       - ReDoc"
echo "" 