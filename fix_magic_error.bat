@echo off
echo Fixing python-magic library issue on Windows...

echo Uninstalling problematic python-magic...
python -m pip uninstall python-magic -y

echo Installing Windows-compatible python-magic-bin...
python -m pip install python-magic-bin==0.4.14

echo Verifying installation...
python -c "import magic; print('✓ python-magic-bin installed successfully')" 2>nul
if errorlevel 1 (
    echo ✗ Failed to install python-magic-bin
    echo.
    echo Alternative solution: Installing file-magic...
    python -m pip install file-magic
    echo ✓ Installed file-magic as alternative
)

echo.
echo Fix applied! You can now run:
echo   python manage.py runserver
echo.
pause 