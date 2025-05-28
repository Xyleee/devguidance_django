# DevGuidance Render Deployment Checklist

## Pre-Deployment Checklist

### ✅ Project Configuration
- [ ] All configuration files created:
  - [ ] `build.sh` - Build script for static files and migrations
  - [ ] `render.yaml` - Infrastructure as Code configuration (optional)
  - [ ] Updated `requirements.txt` with production dependencies

### ✅ Dependencies
- [ ] Verified `requirements.txt` includes all production dependencies:
  - [ ] `python-decouple==3.8` - Environment variable management
  - [ ] `whitenoise==6.5.0` - Static file serving
  - [ ] `gunicorn==21.2.0` - WSGI server
  - [ ] `django-cors-headers==4.3.1` - CORS support
  - [ ] `dj-database-url==2.1.0` - Database URL parsing
  - [ ] `drf-spectacular==0.27.0` - API documentation

### ✅ Django Settings
- [ ] Updated `settings.py` for production:
  - [ ] Environment variable configuration with `python-decouple`
  - [ ] Database configuration with `DATABASE_URL` support
  - [ ] CORS middleware and settings
  - [ ] WhiteNoise middleware for static files
  - [ ] Security settings for production
  - [ ] Static files configuration optimized for Render

### ✅ Code Repository
- [ ] All code committed to Git
- [ ] Repository pushed to GitHub/GitLab
- [ ] `.gitignore` updated to exclude sensitive files
- [ ] `build.sh` file has executable permissions

## Database Setup Options

### Option A: Render PostgreSQL (Recommended)
- [ ] Plan to create PostgreSQL database in Render dashboard
- [ ] Choose appropriate plan (Free/Starter/Standard)
- [ ] Note that free tier has 90-day data retention

### Option B: External Database Provider
- [ ] External PostgreSQL database created (Neon, Supabase, Railway)
- [ ] Connection string obtained
- [ ] Database allows external connections
- [ ] SSL connection configured

## Render Deployment Steps

### 1. Create Render Account and Services

#### Web Service Creation
- [ ] Render account created at [dashboard.render.com](https://dashboard.render.com)
- [ ] Clicked "New +" button
- [ ] Selected "Web Service"
- [ ] Connected GitHub/GitLab repository
- [ ] Repository permissions granted to Render

#### Web Service Configuration
- [ ] Service name: `devguidance-api` (or your preferred name)
- [ ] Environment: `Python 3`
- [ ] Region: Selected appropriate region
- [ ] Branch: `main` (or your production branch)
- [ ] Build Command: `./build.sh`
- [ ] Start Command: `gunicorn devguidance_django.wsgi:application`
- [ ] Instance Type: Selected plan (Free for testing, Starter+ for production)

#### Database Service Creation (if using Render PostgreSQL)
- [ ] Clicked "New +" button
- [ ] Selected "PostgreSQL"
- [ ] Database name: `devguidance-db`
- [ ] User: `devguidance_user`
- [ ] Plan: Selected appropriate plan
- [ ] Region: Same as web service
- [ ] Connection details noted

### 2. Environment Variables Configuration

#### Required Environment Variables
- [ ] `SECRET_KEY` - Django secret key (generated or custom)
- [ ] `DEBUG` - Set to `False`
- [ ] `ALLOWED_HOSTS` - Set to `.onrender.com,your-custom-domain.com`
- [ ] `DATABASE_URL` - PostgreSQL connection string
- [ ] `CORS_ALLOWED_ORIGINS` - Frontend domains
- [ ] `CSRF_TRUSTED_ORIGINS` - Trusted domains

#### Optional Environment Variables
- [ ] `CORS_ALLOW_ALL_ORIGINS` - Set to `False` for production
- [ ] `SECURE_SSL_REDIRECT` - Set to `True` for HTTPS redirect
- [ ] Custom API keys (if using external services)

### 3. Initial Deployment
- [ ] Environment variables configured in Render dashboard
- [ ] First deployment triggered automatically
- [ ] Build process completed successfully (check logs)
- [ ] Database migrations executed successfully
- [ ] Static files collected and served
- [ ] Health check passed

## Post-Deployment Testing

### ✅ Basic Functionality
- [ ] Service is accessible at Render URL
- [ ] Health check endpoint responds: `https://your-service.onrender.com/api/docs/`
- [ ] Static files loading correctly (CSS/JS)
- [ ] No 500 errors in initial load

### ✅ API Endpoints Testing
- [ ] Swagger documentation accessible: `/api/docs/`
- [ ] ReDoc documentation accessible: `/api/redoc/`
- [ ] OpenAPI schema accessible: `/api/schema/`
- [ ] Admin panel accessible: `/admin/`

### ✅ Authentication Testing
- [ ] User registration endpoint working: `POST /api/users/api/register/`
- [ ] Token obtain endpoint working: `POST /api/token/`
- [ ] Token refresh endpoint working: `POST /api/token/refresh/`
- [ ] Protected endpoints require authentication
- [ ] JWT tokens properly validated

### ✅ Database Operations
- [ ] User registration creates database records
- [ ] CRUD operations working for all models
- [ ] Database relationships functioning correctly
- [ ] File uploads storing correctly
- [ ] Data persistence across service restarts

### ✅ File Handling
- [ ] Profile photo uploads working
- [ ] Message file attachments working
- [ ] File size validations enforced
- [ ] File type restrictions working
- [ ] Media files served correctly

## Security and Performance

### ✅ Security Configuration
- [ ] HTTPS enabled (automatic with Render)
- [ ] CORS properly configured for frontend domains
- [ ] CSRF protection enabled
- [ ] Rate limiting functional
- [ ] SQL injection protection verified
- [ ] XSS protection headers present

### ✅ Performance Optimization
- [ ] Static files compressed and served efficiently
- [ ] Database queries optimized
- [ ] Response times acceptable (<2 seconds for API calls)
- [ ] Memory usage within service limits
- [ ] No memory leaks detected

## Monitoring and Maintenance

### ✅ Monitoring Setup
- [ ] Render dashboard monitoring enabled
- [ ] Service logs accessible and readable
- [ ] Error tracking configured
- [ ] Performance metrics reviewed
- [ ] Uptime monitoring active

### ✅ Backup and Recovery
- [ ] Database backup strategy confirmed
- [ ] Environment variables documented
- [ ] Recovery procedures tested
- [ ] Data export/import verified

## Custom Domain Configuration (Optional)

### ✅ Domain Setup
- [ ] Custom domain purchased and configured
- [ ] Domain added in Render dashboard
- [ ] DNS records configured correctly
- [ ] SSL certificate automatically provisioned
- [ ] Domain redirects working properly

## Team and Access Management

### ✅ Team Configuration
- [ ] Team members added to Render project
- [ ] Appropriate permissions assigned
- [ ] Collaboration settings configured
- [ ] Deployment notifications set up

## Production Readiness

### ✅ Final Production Checks
- [ ] Service plan upgraded from Free (if needed)
- [ ] Database plan appropriate for production load
- [ ] Monitoring and alerting configured
- [ ] Backup and disaster recovery procedures documented
- [ ] Performance benchmarks established
- [ ] Security audit completed

## Troubleshooting Quick Reference

### Common Issues and Solutions

#### Build Failures
```bash
# Check build logs in Render dashboard
# Verify build.sh permissions
chmod +x build.sh

# Test build locally
./build.sh
```

#### Database Connection Issues
```bash
# Test DATABASE_URL format
# Ensure database service is running
# Check network connectivity between services
```

#### Static File Issues
```bash
# Verify WhiteNoise configuration
# Check STATIC_ROOT and STATIC_URL settings
# Ensure collectstatic runs in build process
```

#### Memory Issues
```bash
# Monitor resource usage in dashboard
# Optimize database queries
# Consider upgrading service plan
```

## Post-Deployment URLs

After successful deployment, your services will be available at:

- **Main API**: `https://your-service-name.onrender.com/`
- **Swagger Docs**: `https://your-service-name.onrender.com/api/docs/`
- **ReDoc**: `https://your-service-name.onrender.com/api/redoc/`
- **Admin Panel**: `https://your-service-name.onrender.com/admin/`

## Support Resources

- [Render Documentation](https://render.com/docs)
- [Django on Render Guide](https://render.com/docs/deploy-django)
- [Render Community](https://community.render.com)
- [Render Status](https://status.render.com)

## Quick Commands for Local Testing

```bash
# Test production settings
python manage.py check --deploy

# Test static file collection
python manage.py collectstatic --noinput

# Test database migrations
python manage.py migrate --check

# Generate new secret key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

**Note**: Keep this checklist updated as you add new features or change deployment requirements. Render's simplicity makes it an excellent choice for Django applications. 