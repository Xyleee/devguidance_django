# DevGuidance Django - Local Development Guide

This guide ensures your local development environment continues to work seamlessly alongside your production deployment on Render.

## Quick Start for Local Development

### 1. Set Up Local Environment Variables

Copy the local environment template to create your `.env` file:

```bash
cp local.env .env
```

Your `.env` file should contain:
```
# Django Settings for Local Development
SECRET_KEY=django-insecure-9lm*)es%5eex%6p+16#0^80)aq-$3^f#uder_zmi03(_e(n6_u
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# Local Database Settings (PostgreSQL)
DB_NAME=devguidance
DB_USER=myuser
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432

# Local Development Flag
RENDER=False
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run Local Development Server

```bash
python manage.py runserver
```

Your local app will be available at: `http://127.0.0.1:8000/`

## How Local & Production Environments Work Together

### Environment Variable Priority

The settings are configured to work in this priority order:

1. **Environment Variables** (`.env` file for local, Render dashboard for production)
2. **Default Values** (fallback for local development)

### Local Development Features

✅ **DEBUG Mode Enabled** - Full error pages and debugging
✅ **Local Database** - Uses your local PostgreSQL instance
✅ **Local Static Files** - Served by Django development server
✅ **Hot Reload** - Automatic server restart on code changes
✅ **Admin Panel** - Available at `http://127.0.0.1:8000/admin/`
✅ **API Documentation** - Available at `http://127.0.0.1:8000/swagger/`

### Production Features (Render)

✅ **DEBUG Mode Disabled** - Secure error handling
✅ **Production Database** - Render PostgreSQL instance
✅ **Static Files via WhiteNoise** - Optimized static file serving
✅ **Security Headers** - HTTPS, HSTS, XSS protection
✅ **Environment Variables** - Secure configuration via Render dashboard

## Local Development Commands

### Database Management
```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Reset database (if needed)
python manage.py flush

# Make new migrations
python manage.py makemigrations
```

### Testing
```bash
# Run tests
python manage.py test

# Run specific app tests
python manage.py test users
```

### Development Server
```bash
# Standard development server
python manage.py runserver

# Run on different port
python manage.py runserver 8080

# Run on all interfaces (for testing from other devices)
python manage.py runserver 0.0.0.0:8000
```

## Local API Testing

Your local API endpoints:

- **Registration**: `POST http://127.0.0.1:8000/api/register/`
- **Login**: `POST http://127.0.0.1:8000/api/token/`
- **Swagger Docs**: `GET http://127.0.0.1:8000/swagger/`
- **Admin Panel**: `GET http://127.0.0.1:8000/admin/`

### Sample API Test with curl

```bash
# Register a new user
curl -X POST http://127.0.0.1:8000/api/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123",
    "password2": "testpass123",
    "user_type": "student"
  }'

# Get JWT token
curl -X POST http://127.0.0.1:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123"
  }'
```

## Switching Between Environments

### For Local Development
1. Use `.env` file with `DEBUG=True`
2. Run `python manage.py runserver`
3. Access `http://127.0.0.1:8000/`

### For Production Testing
1. Environment variables set in Render dashboard
2. `DEBUG=False` in production
3. Access your Render URL

## Troubleshooting Local Development

### Common Issues

**1. Database Connection Error**
```
# Ensure PostgreSQL is running locally
# Check database credentials in .env file
# Create database if it doesn't exist
```

**2. Static Files Not Loading**
```bash
# Collect static files
python manage.py collectstatic

# Or just use development server (handles static files automatically)
python manage.py runserver
```

**3. Module Import Errors**
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Check virtual environment is activated
```

**4. Migration Issues**
```bash
# Apply migrations
python manage.py migrate

# If tables exist error, try:
python manage.py migrate --fake-initial
```

### Environment Variables Not Loading

If your `.env` file isn't being loaded:

1. Ensure `python-dotenv` is installed: `pip install python-dotenv`
2. Check `.env` file exists in project root
3. Verify no syntax errors in `.env` file
4. Restart development server

## File Structure

```
devguidance_django/
├── .env                    # Local environment variables (not in git)
├── local.env              # Template for local environment
├── env.example            # Template for production environment
├── DEPLOYMENT.md          # Production deployment guide
├── LOCAL_DEVELOPMENT.md   # This file
├── manage.py
├── requirements.txt
├── build.sh              # Render build script
├── runtime.txt           # Python version for Render
└── devguidance_django/
    └── settings.py       # Unified settings for local & production
```

## Security Notes

- ✅ `.env` is in `.gitignore` - won't be committed to repository
- ✅ Production uses different SECRET_KEY
- ✅ DEBUG is False in production
- ✅ Local development uses safe defaults

## Next Steps

1. Create your `.env` file from `local.env`
2. Start local development with `python manage.py runserver`
3. Deploy to production following `DEPLOYMENT.md`
4. Both environments will work independently! 