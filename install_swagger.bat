@echo off
echo Installing DevGuidance Django API with Swagger UI...

REM Activate virtual environment (if exists)
if exist ..\Scripts\activate.bat (
    echo Activating virtual environment...
    call ..\Scripts\activate.bat
)

echo Installing required packages...
python -m pip install --upgrade pip
python -m pip install drf-yasg==1.21.7
python -m pip install packaging

echo Verifying installation...
python -c "import drf_yasg; print('✓ drf-yasg installed successfully')" 2>nul
if errorlevel 1 (
    echo ✗ Failed to install drf-yasg
    pause
    exit /b 1
)

echo Running Django migrations...
python manage.py makemigrations
python manage.py migrate

echo Setup complete!
echo.
echo To start the server, run:
echo   python manage.py runserver
echo.
echo Then visit:
echo   http://localhost:8000/swagger/     - Swagger UI
echo   http://localhost:8000/redoc/       - ReDoc
echo.
pause 