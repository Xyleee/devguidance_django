# DevGuidance API - Complete Test Cases Documentation

This document provides comprehensive test cases for all DevGuidance API endpoints. All examples include copy-pasteable cURL commands and expected responses.

## Base URLs
- **Local**: `http://127.0.0.1:8000`
- **Production**: `https://your-app-name.onrender.com`

## Table of Contents
1. [Authentication Endpoints](#authentication-endpoints)
2. [User Registration](#user-registration)
3. [Student Profile Management](#student-profile-management)
4. [Mentor Profile Management](#mentor-profile-management)
5. [Student Projects](#student-projects)
6. [Mentorship Requests](#mentorship-requests)
7. [Messaging System](#messaging-system)
8. [Admin & Utility](#admin--utility)

---

## Authentication Endpoints

### 1. Get JWT Token (Login)

**Endpoint:** `POST /api/token/`

**Purpose:** Authenticate user and get access/refresh tokens

**Test Case 1: Valid Login**
```bash
curl -X POST http://127.0.0.1:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123"
  }'
```

**Expected Response (200):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Test Case 2: Invalid Credentials**
```bash
curl -X POST http://127.0.0.1:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "wronguser",
    "password": "wrongpass"
  }'
```

**Expected Response (401):**
```json
{
  "detail": "No active account found with the given credentials"
}
```

### 2. Refresh JWT Token

**Endpoint:** `POST /api/token/refresh/`

**Test Case: Valid Refresh**
```bash
curl -X POST http://127.0.0.1:8000/api/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }'
```

**Expected Response (200):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

---

## User Registration

### 3. Register Student

**Endpoint:** `POST /api/register/`

**Test Case 1: Valid Student Registration**
```bash
curl -X POST http://127.0.0.1:8000/api/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "student123",
    "email": "student@example.com",
    "password": "securepass123",
    "password2": "securepass123",
    "user_type": "student"
  }'
```

**Expected Response (201):**
```json
{
  "user": {
    "id": 1,
    "username": "student123",
    "email": "student@example.com"
  },
  "profile": {
    "id": 1,
    "name": "",
    "bio": "",
    "tech_stack": [],
    "learning_goals": "",
    "experience_level": "beginner"
  },
  "message": "Student account created successfully"
}
```

### 4. Register Mentor

**Test Case: Valid Mentor Registration**
```bash
curl -X POST http://127.0.0.1:8000/api/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "mentor123",
    "email": "mentor@example.com",
    "password": "securepass123",
    "password2": "securepass123",
    "user_type": "mentor"
  }'
```

**Expected Response (201):**
```json
{
  "user": {
    "id": 2,
    "username": "mentor123",
    "email": "mentor@example.com"
  },
  "profile": {
    "id": 1,
    "name": "",
    "bio": "",
    "expertise_tags": [],
    "years_experience": 0,
    "company": ""
  },
  "message": "Mentor account created successfully"
}
```

**Test Case: Password Mismatch**
```bash
curl -X POST http://127.0.0.1:8000/api/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123",
    "password2": "differentpass",
    "user_type": "student"
  }'
```

**Expected Response (400):**
```json
{
  "password2": ["Passwords must match."]
}
```

---

## Student Profile Management

### 5. Get My Student Profile

**Endpoint:** `GET /api/users/api/student-profiles/me/`

**Test Case: Get Own Profile**
```bash
curl -X GET http://127.0.0.1:8000/api/users/api/student-profiles/me/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

**Expected Response (200):**
```json
{
  "id": 1,
  "user": {
    "id": 1,
    "username": "student123",
    "email": "student@example.com"
  },
  "name": "John Doe",
  "bio": "Computer Science student learning web development",
  "tech_stack": ["Python", "JavaScript", "React"],
  "learning_goals": "Master full-stack development",
  "experience_level": "intermediate",
  "profile_picture": null,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### 6. Update Student Profile

**Endpoint:** `PUT /api/users/api/student-profiles/me/`

**Test Case: Update Profile**
```bash
curl -X PUT http://127.0.0.1:8000/api/users/api/student-profiles/me/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe Updated",
    "bio": "Passionate CS student focusing on AI and web development",
    "tech_stack": ["Python", "JavaScript", "React", "Django", "PostgreSQL"],
    "learning_goals": "Build production-ready applications and understand ML",
    "experience_level": "intermediate"
  }'
```

**Expected Response (200):**
```json
{
  "id": 1,
  "user": {
    "id": 1,
    "username": "student123",
    "email": "student@example.com"
  },
  "name": "John Doe Updated",
  "bio": "Passionate CS student focusing on AI and web development",
  "tech_stack": ["Python", "JavaScript", "React", "Django", "PostgreSQL"],
  "learning_goals": "Build production-ready applications and understand ML",
  "experience_level": "intermediate",
  "profile_picture": null,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T12:45:00Z"
}
```

### 7. Search Student Profiles

**Endpoint:** `GET /api/users/api/student-profiles/?search=python`

**Test Case: Search by Tech Stack**
```bash
curl -X GET "http://127.0.0.1:8000/api/users/api/student-profiles/?search=python" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

**Expected Response (200):**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "user": {
        "id": 1,
        "username": "student123",
        "email": "student@example.com"
      },
      "name": "John Doe",
      "bio": "CS student learning Python",
      "tech_stack": ["Python", "Django"],
      "learning_goals": "Backend development",
      "experience_level": "beginner"
    }
  ]
}
```

---

## Mentor Profile Management

### 8. Get All Mentors (Public)

**Endpoint:** `GET /api/users/api/mentor-profiles/`

**Test Case: List All Mentors**
```bash
curl -X GET http://127.0.0.1:8000/api/users/api/mentor-profiles/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

**Expected Response (200):**
```json
{
  "count": 3,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "user": {
        "id": 2,
        "username": "mentor123",
        "email": "mentor@example.com"
      },
      "name": "Jane Smith",
      "bio": "Senior Software Engineer with 8 years experience",
      "expertise_tags": ["Python", "Django", "React", "AWS"],
      "years_experience": 8,
      "company": "Tech Corp",
      "linkedin_profile": "https://linkedin.com/in/janesmith",
      "availability_status": "available",
      "profile_picture": null
    }
  ]
}
```

### 9. Get My Mentor Profile

**Endpoint:** `GET /api/users/api/mentor-profiles/me/`

**Test Case: Get Own Mentor Profile**
```bash
curl -X GET http://127.0.0.1:8000/api/users/api/mentor-profiles/me/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

### 10. Update Mentor Profile

**Endpoint:** `PUT /api/users/api/mentor-profiles/me/`

**Test Case: Update Mentor Profile**
```bash
curl -X PUT http://127.0.0.1:8000/api/users/api/mentor-profiles/me/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane Smith",
    "bio": "Senior Full-Stack Developer specializing in Python and React",
    "expertise_tags": ["Python", "Django", "React", "PostgreSQL", "AWS", "Docker"],
    "years_experience": 8,
    "company": "Tech Innovations Inc",
    "linkedin_profile": "https://linkedin.com/in/janesmith",
    "availability_status": "available"
  }'
```

### 11. Search Mentors by Expertise

**Endpoint:** `GET /api/users/api/mentor-profiles/by_expertise/?tag=Python`

**Test Case: Find Python Mentors**
```bash
curl -X GET "http://127.0.0.1:8000/api/users/api/mentor-profiles/by_expertise/?tag=Python" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

---

## Student Projects

### 12. Create Student Project

**Endpoint:** `POST /api/users/api/student-projects/`

**Test Case: Create New Project**
```bash
curl -X POST http://127.0.0.1:8000/api/users/api/student-projects/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "title": "E-commerce Web App",
    "description": "Full-stack e-commerce platform built with Django and React",
    "technologies_used": ["Django", "React", "PostgreSQL", "Redux"],
    "github_url": "https://github.com/student123/ecommerce-app",
    "live_demo_url": "https://myecommerce.herokuapp.com",
    "status": "in_progress"
  }'
```

**Expected Response (201):**
```json
{
  "id": 1,
  "student": {
    "id": 1,
    "name": "John Doe",
    "user": {
      "username": "student123"
    }
  },
  "title": "E-commerce Web App",
  "description": "Full-stack e-commerce platform built with Django and React",
  "technologies_used": ["Django", "React", "PostgreSQL", "Redux"],
  "github_url": "https://github.com/student123/ecommerce-app",
  "live_demo_url": "https://myecommerce.herokuapp.com",
  "status": "in_progress",
  "created_at": "2024-01-15T14:30:00Z",
  "updated_at": "2024-01-15T14:30:00Z"
}
```

### 13. Get My Projects

**Endpoint:** `GET /api/users/api/student-projects/`

**Test Case: List Own Projects**
```bash
curl -X GET http://127.0.0.1:8000/api/users/api/student-projects/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

### 14. Update Project

**Endpoint:** `PUT /api/users/api/student-projects/{id}/`

**Test Case: Update Project Status**
```bash
curl -X PUT http://127.0.0.1:8000/api/users/api/student-projects/1/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "title": "E-commerce Web App",
    "description": "Full-stack e-commerce platform with payment integration",
    "technologies_used": ["Django", "React", "PostgreSQL", "Redux", "Stripe"],
    "github_url": "https://github.com/student123/ecommerce-app",
    "live_demo_url": "https://myecommerce.herokuapp.com",
    "status": "completed"
  }'
```

---

## Mentorship Requests

### 15. Create Mentorship Request

**Endpoint:** `POST /api/users/api/mentorship-requests/`

**Test Case: Send Mentorship Request**
```bash
curl -X POST http://127.0.0.1:8000/api/users/api/mentorship-requests/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "mentor": 2,
    "message": "Hi! I am learning Django and would love your guidance on best practices and career advice. I have been coding for 6 months and working on an e-commerce project.",
    "learning_objectives": "Master Django REST API development, Learn deployment strategies, Get career guidance"
  }'
```

**Expected Response (201):**
```json
{
  "id": 1,
  "student": {
    "id": 1,
    "username": "student123",
    "email": "student@example.com"
  },
  "mentor": {
    "id": 2,
    "username": "mentor123",
    "email": "mentor@example.com"
  },
  "message": "Hi! I am learning Django and would love your guidance...",
  "learning_objectives": "Master Django REST API development, Learn deployment strategies, Get career guidance",
  "status": "pending",
  "rejection_reason": "",
  "created_at": "2024-01-15T15:00:00Z",
  "updated_at": "2024-01-15T15:00:00Z"
}
```

### 16. Get Student's Requests

**Endpoint:** `GET /api/users/api/mentorship-requests/student/`

**Test Case: View My Sent Requests**
```bash
curl -X GET http://127.0.0.1:8000/api/users/api/mentorship-requests/student/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

### 17. Get Mentor's Requests

**Endpoint:** `GET /api/users/api/mentorship-requests/mentor/`

**Test Case: View Received Requests (Mentor)**
```bash
curl -X GET http://127.0.0.1:8000/api/users/api/mentorship-requests/mentor/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

### 18. Accept Mentorship Request

**Endpoint:** `PATCH /api/users/api/mentorship-requests/{id}/accept/`

**Test Case: Accept Request (Mentor)**
```bash
curl -X PATCH http://127.0.0.1:8000/api/users/api/mentorship-requests/1/accept/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Expected Response (200):**
```json
{
  "id": 1,
  "student": {
    "id": 1,
    "username": "student123",
    "email": "student@example.com"
  },
  "mentor": {
    "id": 2,
    "username": "mentor123",
    "email": "mentor@example.com"
  },
  "message": "Hi! I am learning Django...",
  "learning_objectives": "Master Django REST API development...",
  "status": "accepted",
  "rejection_reason": "",
  "created_at": "2024-01-15T15:00:00Z",
  "updated_at": "2024-01-15T15:30:00Z"
}
```

### 19. Decline Mentorship Request

**Endpoint:** `PATCH /api/users/api/mentorship-requests/{id}/decline/`

**Test Case: Decline with Reason**
```bash
curl -X PATCH http://127.0.0.1:8000/api/users/api/mentorship-requests/1/decline/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "rejection_reason": "Thank you for your interest! Unfortunately, I am currently at capacity with mentees. I recommend checking out our other Python mentors."
  }'
```

---

## Messaging System

### 20. Send Message

**Endpoint:** `POST /api/users/messages/`

**Test Case: Send Message to Mentor**
```bash
curl -X POST http://127.0.0.1:8000/api/users/messages/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "receiver": 2,
    "content": "Hi Jane! Thank you for accepting my mentorship request. I would love to schedule our first session. When would be a good time for you?"
  }'
```

**Expected Response (201):**
```json
{
  "id": 1,
  "sender": {
    "id": 1,
    "username": "student123"
  },
  "receiver": {
    "id": 2,
    "username": "mentor123"
  },
  "content": "Hi Jane! Thank you for accepting my mentorship request...",
  "timestamp": "2024-01-15T16:00:00Z",
  "is_read": false
}
```

### 21. Get Message History

**Endpoint:** `GET /api/users/messages/{user_id}/`

**Test Case: Get Conversation with Mentor**
```bash
curl -X GET http://127.0.0.1:8000/api/users/messages/2/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

**Expected Response (200):**
```json
[
  {
    "id": 1,
    "sender": {
      "id": 1,
      "username": "student123"
    },
    "receiver": {
      "id": 2,
      "username": "mentor123"
    },
    "content": "Hi Jane! Thank you for accepting my mentorship request...",
    "timestamp": "2024-01-15T16:00:00Z",
    "is_read": false
  },
  {
    "id": 2,
    "sender": {
      "id": 2,
      "username": "mentor123"
    },
    "receiver": {
      "id": 1,
      "username": "student123"
    },
    "content": "Hi John! I'm excited to work with you. How about we schedule a call for Thursday at 2 PM?",
    "timestamp": "2024-01-15T16:15:00Z",
    "is_read": true
  }
]
```

---

## Admin & Utility

### 22. Protected Endpoint Test

**Endpoint:** `GET /api/users/protected/`

**Test Case: Access Protected Content**
```bash
curl -X GET http://127.0.0.1:8000/api/users/protected/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

**Expected Response (200):**
```json
{
  "message": "Hello, student123! This is protected content."
}
```

### 23. Mentor List for Students

**Endpoint:** `GET /api/users/api/mentors/`

**Test Case: Browse Available Mentors**
```bash
curl -X GET http://127.0.0.1:8000/api/users/api/mentors/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

---

## Error Test Cases

### 24. Authentication Errors

**Test Case: Missing Token**
```bash
curl -X GET http://127.0.0.1:8000/api/users/api/student-profiles/me/
```

**Expected Response (401):**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

**Test Case: Invalid Token**
```bash
curl -X GET http://127.0.0.1:8000/api/users/api/student-profiles/me/ \
  -H "Authorization: Bearer invalid_token_here"
```

**Expected Response (401):**
```json
{
  "detail": "Given token not valid for any token type",
  "code": "token_not_valid",
  "messages": [
    {
      "token_class": "AccessToken",
      "token_type": "access",
      "message": "Token is invalid or expired"
    }
  ]
}
```

### 25. Permission Errors

**Test Case: Student Accessing Mentor Endpoint**
```bash
curl -X GET http://127.0.0.1:8000/api/users/api/mentorship-requests/mentor/ \
  -H "Authorization: Bearer {student_token}"
```

**Expected Response (403):**
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 26. Validation Errors

**Test Case: Invalid Email Format**
```bash
curl -X POST http://127.0.0.1:8000/api/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "invalid-email",
    "password": "password123",
    "password2": "password123",
    "user_type": "student"
  }'
```

**Expected Response (400):**
```json
{
  "email": ["Enter a valid email address."]
}
```

---

## Rate Limiting Tests

### 27. Rate Limit Test

**Test Case: Exceed Registration Rate Limit**
```bash
# Run this command multiple times quickly (more than 5 times in 60 seconds)
curl -X POST http://127.0.0.1:8000/api/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser1",
    "email": "test1@example.com",
    "password": "password123",
    "password2": "password123",
    "user_type": "student"
  }'
```

**Expected Response (429) after 5 requests:**
```json
{
  "detail": "Rate limit exceeded. Try again later."
}
```

---

## Testing Tips

### Environment Variables for Testing
```bash
# Set base URL for easier testing
export BASE_URL="http://127.0.0.1:8000"

# Store token for reuse
export TOKEN="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."

# Example with environment variables
curl -X GET "$BASE_URL/api/users/protected/" \
  -H "Authorization: Bearer $TOKEN"
```

### Postman Collection
Import these cURL commands into Postman for GUI testing:
1. Create new collection "DevGuidance API"
2. Add requests from above test cases
3. Set up environment variables for base URL and tokens
4. Use collection runner for automated testing

### Testing Sequence Recommendation
1. Register users (student and mentor)
2. Login and get tokens
3. Update profiles
4. Create student projects
5. Send mentorship requests
6. Accept/decline requests
7. Send messages
8. Test search and filtering

This documentation provides comprehensive test coverage for all API endpoints with copy-pasteable examples! 