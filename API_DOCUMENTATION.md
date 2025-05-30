# DevGuidance API Documentation

## Project Overview

DevGuidance is a mentorship platform that connects developers (students) with experienced mentors. The API provides comprehensive functionality for user registration, profile management, mentorship requests, and real-time messaging.

## Features

- **User Authentication**: JWT-based authentication with student/mentor roles
- **Profile Management**: Separate profiles for students and mentors with different capabilities
- **Mentorship System**: Request-based mentorship matching with acceptance/rejection workflow
- **Project Portfolio**: Students can showcase their projects
- **Real-time Messaging**: Communication between matched mentors and students
- **Expert Search**: Filter mentors by expertise tags
- **Rate Limiting**: Built-in protection against abuse

## Technology Stack

- **Backend**: Django 5.1.6 + Django REST Framework
- **Authentication**: JWT (djangorestframework-simplejwt)
- **Documentation**: drf-yasg (Swagger/OpenAPI)
- **Database**: PostgreSQL
- **Real-time**: Server-Sent Events (SSE) for messaging

## API Endpoints

### Authentication Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/users/register/` | Register new user (student/mentor) | No |
| POST | `/api/token/` | Obtain JWT access token | No |
| POST | `/api/token/refresh/` | Refresh JWT token | No |
| GET | `/api/users/protected/` | Test authentication | Yes |

### Student Profile Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/users/api/student-profiles/` | List student profiles | Yes |
| POST | `/api/users/api/student-profiles/` | Create/update student profile | Yes |
| GET | `/api/users/api/student-profiles/me/` | Get current user's profile | Yes |

### Mentor Profile Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/users/api/mentor-profiles/` | List all mentors | Yes |
| POST | `/api/users/api/mentor-profiles/` | Create/update mentor profile | Yes |
| GET | `/api/users/api/mentor-profiles/me/` | Get current user's profile | Yes |
| GET | `/api/users/api/mentor-profiles/by_expertise/` | Filter mentors by expertise | Yes |

### Student Projects Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/users/api/student-projects/` | List student projects | Yes |
| POST | `/api/users/api/student-projects/` | Create new project | Yes |

### Mentorship Requests Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/users/api/mentorship-requests/` | List requests (filtered by role) | Yes |
| POST | `/api/users/api/mentorship-requests/` | Create mentorship request | Yes |
| PATCH | `/api/users/api/mentorship-requests/{id}/accept/` | Accept request (mentors only) | Yes |
| PATCH | `/api/users/api/mentorship-requests/{id}/decline/` | Decline request (mentors only) | Yes |

### Messaging Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/users/messages/` | Send message | Yes |
| GET | `/api/users/messages/{user_id}/` | Get message history | Yes |
| GET | `/api/users/messages/stream/{user_id}/` | Real-time message stream (SSE) | Yes |

## Data Models

### User Registration
```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "password2": "string",
  "user_type": "student" | "mentor"
}
```

### Student Profile
```json
{
  "name": "string",
  "bio": "string",
  "tech_stack": ["Python", "React", "Django"],
  "github_profile": "string",
  "linkedin_profile": "string",
  "portfolio_website": "string",
  "profile_picture": "file",
  "learning_goals": "string",
  "experience_level": "beginner" | "intermediate" | "advanced"
}
```

### Mentor Profile
```json
{
  "name": "string",
  "bio": "string",
  "expertise_tags": ["Python", "Django", "React"],
  "years_of_experience": "integer",
  "current_position": "string",
  "company": "string",
  "github_profile": "string",
  "linkedin_profile": "string",
  "profile_picture": "file",
  "mentoring_approach": "string",
  "availability": "string"
}
```

### Student Project
```json
{
  "title": "string",
  "description": "string",
  "technologies_used": ["Python", "Django"],
  "github_link": "string",
  "live_demo_link": "string",
  "project_image": "file",
  "completion_status": "completed" | "in_progress" | "planned"
}
```

### Mentorship Request
```json
{
  "mentor": "integer",
  "message": "string",
  "specific_goals": "string",
  "preferred_communication": "string",
  "status": "pending" | "accepted" | "declined"
}
```

### Message
```json
{
  "receiver": "integer",
  "content": "string",
  "timestamp": "datetime"
}
```

## Authentication Flow

1. **Registration**: Users register with `user_type` field
2. **Profile Creation**: Automatic profile creation based on user type
3. **Token Acquisition**: Users login to get JWT access token
4. **API Access**: Include token in Authorization header: `Bearer <token>`

## Business Rules

### Mentorship Requests
- Students can send requests to mentors
- Mentors can accept/decline requests
- Accepting a request automatically declines other pending requests from the same student
- Mentors can have maximum 5 active mentees

### Messaging
- Only users with accepted mentorship relationships can message each other
- Real-time messaging via Server-Sent Events
- Message history is preserved

### Permissions
- Users can only edit their own profiles
- Students can only manage their own projects
- Mentors can only accept/decline requests sent to them

## Error Handling

The API follows standard HTTP status codes:

- `200` - Success
- `201` - Created
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (authentication required)
- `403` - Forbidden (permission denied)
- `404` - Not Found
- `500` - Internal Server Error

Error responses include descriptive messages:
```json
{
  "detail": "Error description",
  "field_errors": {
    "field_name": ["Specific error message"]
  }
}
```

## Rate Limiting

Certain endpoints have rate limiting:
- Registration: 5 requests per minute
- Token obtain: 5 requests per minute
- Token refresh: 10 requests per minute

## Development Setup

1. **Clone and navigate to project**
   ```bash
   cd layugan_activities_BSIT3C/pyenv/devguidance_django
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

4. **Start development server**
   ```bash
   python manage.py runserver
   ```

5. **Access API documentation**
   - Swagger UI: http://localhost:8000/swagger/
   - ReDoc: http://localhost:8000/redoc/

## Testing with Swagger UI

1. Open Swagger UI at http://localhost:8000/swagger/
2. Register a new user (student or mentor)
3. Use the token endpoint to get an access token
4. Click "Authorize" and enter: `Bearer YOUR_TOKEN`
5. Test protected endpoints

## Production Considerations

- Set `DEBUG = False` in production
- Use environment variables for sensitive settings
- Configure proper database settings
- Set up CORS for frontend integration
- Implement proper logging
- Use HTTPS in production
- Consider Redis for caching and session storage

## API Versioning

Current API version: v1
- All endpoints are prefixed with `/api/`
- Future versions will maintain backward compatibility
- Deprecation notices will be provided for breaking changes

## Support

For issues or questions about the API:
1. Check the interactive Swagger documentation
2. Review this documentation
3. Check the Django admin interface for data verification
4. Review server logs for debugging 