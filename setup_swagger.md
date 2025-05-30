# DevGuidance Django API - Swagger UI Setup Guide

## Overview
This guide will help you set up Swagger UI documentation for the DevGuidance Django REST API. The API provides endpoints for user registration, student/mentor profiles, mentorship requests, and messaging.

## Prerequisites
- Python 3.8+
- Django 5.1.6
- Virtual environment activated

## Installation Steps

### 1. Install Required Packages
```bash
pip install drf-yasg packaging
```

Or install all requirements:
```bash
pip install -r requirements.txt
```

### 2. Verify Installation
The following packages should be installed:
- `drf-yasg==1.21.7` - For Swagger UI generation
- `packaging` - Required dependency for drf-yasg

### 3. Database Setup
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser  # Optional: for admin access
```

### 4. Run the Development Server
```bash
python manage.py runserver
```

## Accessing API Documentation

Once the server is running, you can access the API documentation at:

### Swagger UI (Interactive Documentation)
- URL: `http://localhost:8000/swagger/`
- Features: Interactive API testing, request/response examples, authentication support

### ReDoc (Clean Documentation)
- URL: `http://localhost:8000/redoc/`
- Features: Clean, readable documentation format

### OpenAPI Schema (JSON/YAML)
- JSON: `http://localhost:8000/swagger.json`
- YAML: `http://localhost:8000/swagger.yaml`

## API Authentication

The API uses JWT (JSON Web Token) authentication. To use protected endpoints:

1. Register a new user account at `/api/users/register/`
2. Get an access token at `/api/token/`
3. Use the token in Swagger UI:
   - Click the "Authorize" button in Swagger UI
   - Enter: `Bearer YOUR_ACCESS_TOKEN`
   - Click "Authorize"

## Available API Endpoints

### Authentication
- `POST /api/users/register/` - Register as student or mentor
- `POST /api/token/` - Get access token
- `POST /api/token/refresh/` - Refresh access token
- `GET /api/users/protected/` - Test authentication

### Student Profiles
- `GET /api/users/api/student-profiles/` - List student profiles
- `POST /api/users/api/student-profiles/` - Create/update profile
- `GET /api/users/api/student-profiles/me/` - Get current user's profile

### Mentor Profiles
- `GET /api/users/api/mentor-profiles/` - List all mentors
- `POST /api/users/api/mentor-profiles/` - Create/update profile
- `GET /api/users/api/mentor-profiles/me/` - Get current user's profile
- `GET /api/users/api/mentor-profiles/by_expertise/` - Filter by expertise

### Student Projects
- `GET /api/users/api/student-projects/` - List projects
- `POST /api/users/api/student-projects/` - Create project

### Mentorship Requests
- `GET /api/users/api/mentorship-requests/` - List requests
- `POST /api/users/api/mentorship-requests/` - Create request
- `PATCH /api/users/api/mentorship-requests/{id}/accept/` - Accept request (mentors)
- `PATCH /api/users/api/mentorship-requests/{id}/decline/` - Decline request (mentors)

### Messaging
- `POST /api/users/messages/` - Send message
- `GET /api/users/messages/{user_id}/` - Get message history
- `GET /api/users/messages/stream/{user_id}/` - Real-time message stream

## Configuration Details

### Swagger Settings (settings.py)
```python
SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header'
        }
    },
    'USE_SESSION_AUTH': False,
    'JSON_EDITOR': True,
    'SUPPORTED_SUBMIT_METHODS': ['get', 'post', 'put', 'delete', 'patch'],
    'OPERATIONS_SORTER': 'alpha',
    'TAGS_SORTER': 'alpha',
    'DOC_EXPANSION': 'none',
    'DEEP_LINKING': True,
    'SHOW_EXTENSIONS': True,
    'DEFAULT_MODEL_RENDERING': 'example'
}
```

## Troubleshooting

### Common Issues

1. **Module not found errors**
   ```bash
   pip install -r requirements.txt
   ```

2. **Database errors**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

3. **Virtual environment not activated**
   - Windows: `Scripts\activate`
   - Linux/Mac: `source bin/activate`

4. **Swagger not loading**
   - Check that `drf_yasg` is in `INSTALLED_APPS`
   - Verify URL patterns are included
   - Check console for JavaScript errors

### Development Tips

1. **Testing API endpoints**
   - Use Swagger UI for interactive testing
   - Create test users with different roles (student/mentor)
   - Test authentication workflows

2. **Adding custom documentation**
   - Use `@swagger_auto_schema` decorator
   - Add operation descriptions and response schemas
   - Group endpoints with tags

## Example Usage

### 1. Register a Student
```bash
curl -X POST "http://localhost:8000/api/users/register/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "student1",
    "email": "student@example.com",
    "password": "password123",
    "password2": "password123",
    "user_type": "student"
  }'
```

### 2. Get Access Token
```bash
curl -X POST "http://localhost:8000/api/token/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "student1",
    "password": "password123"
  }'
```

### 3. Access Protected Endpoint
```bash
curl -X GET "http://localhost:8000/api/users/protected/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Next Steps

1. Explore the interactive Swagger UI
2. Test different user roles (student vs mentor)
3. Try the messaging system between matched users
4. Review the API documentation for integration 