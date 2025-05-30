# DevGuidance Django - Render Deployment Guide

This guide will help you deploy your DevGuidance Django application to Render.

## Prerequisites

1. A Render account (sign up at [render.com](https://render.com))
2. Your Django project pushed to a Git repository (GitHub, GitLab, or Bitbucket)
3. The project configured with the necessary deployment files (included in this repo)

## Deployment Steps

### 1. Prepare Your Repository

Make sure your repository includes:
- `requirements.txt` - Python dependencies
- `build.sh` - Build script for Render
- `runtime.txt` - Python version specification
- Updated `settings.py` with production configurations

### 2. Create a PostgreSQL Database on Render

1. Log into your Render dashboard
2. Click "New +" and select "PostgreSQL"
3. Give your database a name (e.g., `devguidance-db`)
4. Choose your region and plan
5. Click "Create Database"
6. Once created, note down the database connection details

### 3. Deploy the Web Service

1. In Render dashboard, click "New +" and select "Web Service"
2. Connect your Git repository
3. Configure the service:
   - **Name**: `devguidance-django` (or your preferred name)
   - **Environment**: `Python 3`
   - **Region**: Choose closest to your users
   - **Branch**: `main` or your deployment branch
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn devguidance_django.wsgi:application`

### 4. Set Environment Variables

In the Render dashboard, go to your web service's Environment tab and add:

```
SECRET_KEY=your-generated-secret-key-here
DEBUG=False
DATABASE_URL=your-postgres-connection-string-from-step-2
RENDER=True
```

**Important**: Generate a new SECRET_KEY for production. You can use Django's built-in function:
```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

### 5. Advanced Configuration (Optional)

#### Custom Domain
- In your service settings, you can add a custom domain
- Update `ALLOWED_HOSTS` in your environment variables to include your custom domain

#### Environment Variables Reference
- `SECRET_KEY`: Django secret key (required)
- `DEBUG`: Set to `False` for production
- `DATABASE_URL`: PostgreSQL connection string (automatically provided by Render)
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `RENDER`: Set to `True` (helps identify Render environment)

### 6. Post-Deployment Tasks

After successful deployment:

1. **Create Superuser**: Use Render's shell feature to create an admin user:
   ```bash
   python manage.py createsuperuser
   ```

2. **Test Your API**: Your API will be available at:
   - Main API: `https://your-app-name.onrender.com/api/`
   - Admin Panel: `https://your-app-name.onrender.com/admin/`
   - API Documentation: `https://your-app-name.onrender.com/swagger/`

## API Endpoints

Your deployed application will have the following main endpoints:

- `POST /api/register/` - User registration
- `POST /api/token/` - JWT token authentication
- `POST /api/token/refresh/` - Refresh JWT token
- `GET /api/students/profiles/` - Student profiles
- `GET /api/mentors/profiles/` - Mentor profiles
- `POST /api/mentorship-requests/` - Create mentorship requests
- `GET /api/swagger/` - API documentation

## Troubleshooting

### Common Issues

1. **Build Fails**: Check that all dependencies in `requirements.txt` are correct
2. **Database Connection**: Ensure `DATABASE_URL` is correctly set
3. **Static Files**: Verify `whitenoise` is installed and configured
4. **CORS Issues**: Add frontend domain to `ALLOWED_HOSTS`

### Logs
- Check Render's logs for detailed error information
- Use `print()` statements for debugging (they'll appear in logs)

### Database Issues
- Run migrations manually using Render's shell: `python manage.py migrate`
- Check database connection with: `python manage.py dbshell`

## Security Considerations

1. Never commit sensitive data to Git
2. Use strong, unique SECRET_KEY
3. Keep DEBUG=False in production
4. Regularly update dependencies
5. Use HTTPS (automatically provided by Render)

## Monitoring

- Monitor your application through Render's dashboard
- Set up alerts for downtime or errors
- Consider upgrading to paid plans for better performance and monitoring

## Support

- Render Documentation: [render.com/docs](https://render.com/docs)
- Django Deployment Guide: [docs.djangoproject.com](https://docs.djangoproject.com/en/stable/howto/deployment/)

## Next Steps

1. Set up CI/CD for automatic deployments
2. Configure custom domain
3. Set up monitoring and logging
4. Implement backup strategy for your database
5. Consider CDN for static files 