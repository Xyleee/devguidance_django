# DevGuidance API Documentation

## Installation Requirements

The API requires the following dependencies:
* Python 3.x
* Django and Django REST Framework
* PostgreSQL database
* Python libraries:
  * python-magic or python-magic-bin (on Windows)
  * Pillow for image processing
  * djangorestframework-simplejwt for authentication

## Rate Limiting

The API implements custom rate limiting to prevent abuse. The following endpoints are protected by rate limits:

* **Register User**: 5 requests per 60 seconds
* **Obtain Token**: 5 requests per 60 seconds
* **Refresh Token**: 10 requests per 60 seconds

When a rate limit is exceeded, the API returns:
* **Status Code**: 429 Too Many Requests
* **Response Body**:
  ```json
  {
    "detail": "Rate limit exceeded. Try again in X seconds."
  }
  ```

## Authentication

### Register User

*   **Method:** `POST`
*   **Endpoint:** `/api/users/api/register/`
*   **Rate Limit:** 5 requests per minute
*   **Headers:**
    *   `Content-Type: application/json`
*   **Request Body:**
    ```json
    {
        "username": "newuser",
        "email": "user@example.com",
        "password": "epassword",
        "password2": "epassword",
        "user_type": "student", // Or "mentor"
        "name": "Test User",
        "photo": "base64EncodedImage", // Optional
        "first_name": "Test", // Optional
        "last_name": "User"   // Optional
    }
    ```
*   **Sample Success Response (201 Created):**
    ```json
    {
        "user": {
            "id": 1,
            "username": "newuser",
            "email": "user@example.com"
        },
        "profile": {
            "name": "Test User",
            "bio": "",
            "year_level": 1,
            "tech_stack": [],
            "photo_url": "/media/profile_photos/student/abc123.jpg"
            // Or mentor profile fields
        },
        "message": "User registered successfully as a student."
    }
    ```
*   **Sample Error Response (400 Bad Request):**
    ```json
    {
        "password": [
            "Password fields didn't match."
        ]
        // Or other validation errors
    }
    ```

### Login (Get Token)

*   **Method:** `POST`
*   **Endpoint:** `/api/token/`
*   **Rate Limit:** 5 requests per minute
*   **Headers:**
    *   `Content-Type: application/json`
*   **Request Body:**
    ```json
    {
        "username": "newuser",
        "password": "epassword"
    }
    ```
*   **Sample Success Response (200 OK):**
    ```json
    {
        "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    ```

### Refresh Token

*   **Method:** `POST`
*   **Endpoint:** `/api/token/refresh/`
*   **Rate Limit:** 10 requests per minute
*   **Headers:**
    *   `Content-Type: application/json`
*   **Request Body:**
    ```json
    {
        "refresh": "your_refresh_token"
    }
    ```
*   **Sample Success Response (200 OK):**
    ```json
    {
        "access": "new_access_token..."
    }
    ```

## Student Resources

### Student Profile Management

*   **Get My Profile**
    *   **Method:** `GET`
    *   **Endpoint:** `/api/users/api/student-profiles/me/`
    *   **Headers:** `Authorization: Bearer <token>`
    *   **Response (200 OK):**
        ```json
        {
            "id": 1,
            "name": "Student Name",
            "bio": "Student bio",
            "year_level": 2,
            "tech_stack": ["Python", "Django", "React"],
            "photo_url": "/media/profile_photos/student/abc123.jpg",
            "created_at": "2023-06-01T12:00:00Z",
            "updated_at": "2023-06-02T12:00:00Z"
        }
        ```

*   **Update Profile**
    *   **Method:** `PUT/PATCH`
    *   **Endpoint:** `/api/users/api/student-profiles/<id>/`
    *   **Headers:** 
        * `Authorization: Bearer <token>`
        * `Content-Type: multipart/form-data` (for photo upload)
    *   **Request Body:**
        ```json
        {
            "name": "Updated Name",
            "bio": "New bio",
            "year_level": 3,
            "tech_stack": ["Python", "Django", "React", "NextJS"],
            "photo": "[file upload]"  // Optional
        }
        ```

### Student Projects

*   **List My Projects**
    *   **Method:** `GET`
    *   **Endpoint:** `/api/users/api/student-projects/`
    *   **Headers:** `Authorization: Bearer <token>`

*   **Create Project**
    *   **Method:** `POST`
    *   **Endpoint:** `/api/users/api/student-projects/`
    *   **Headers:** `Authorization: Bearer <token>`
    *   **Request Body:**
        ```json
        {
            "title": "My Project",
            "description": "Project description",
            "tools_used": ["Python", "Django"]
        }
        ```

*   **Update Project**
    *   **Method:** `PUT/PATCH`
    *   **Endpoint:** `/api/users/api/student-projects/<id>/`
    *   **Headers:** `Authorization: Bearer <token>`

*   **Delete Project**
    *   **Method:** `DELETE`
    *   **Endpoint:** `/api/users/api/student-projects/<id>/`
    *   **Headers:** `Authorization: Bearer <token>`

### Browse Mentors

*   **List All Mentors**
    *   **Method:** `GET`
    *   **Endpoint:** `/api/users/api/mentors/`
    *   **Headers:** `Authorization: Bearer <token>`
    *   **Query Parameters:**
        * `search`: Search mentors by name or expertise tags

*   **Find Mentors by Expertise**
    *   **Method:** `GET`
    *   **Endpoint:** `/api/users/api/mentor-profiles/by_expertise/`
    *   **Headers:** `Authorization: Bearer <token>`
    *   **Query Parameters:**
        * `tag`: Expertise tag to filter by

## Mentor Resources

### Mentor Profile Management

*   **Get My Profile**
    *   **Method:** `GET`
    *   **Endpoint:** `/api/users/api/mentor-profiles/me/`
    *   **Headers:** `Authorization: Bearer <token>`

*   **Update Profile**
    *   **Method:** `PUT/PATCH`
    *   **Endpoint:** `/api/users/api/mentor-profiles/<id>/`
    *   **Headers:** 
        * `Authorization: Bearer <token>`
        * `Content-Type: multipart/form-data` (for photo upload)
    *   **Request Body:**
        ```json
        {
            "name": "Mentor Name",
            "bio": "Mentor bio",
            "experience_years": 5,
            "expertise_tags": ["Python", "Django", "Machine Learning"],
            "photo": "[file upload]"  // Optional
        }
        ```

## Mentorship System

### Mentorship Requests

*   **Student: Send Request**
    *   **Method:** `POST`
    *   **Endpoint:** `/api/users/api/mentorship-requests/`
    *   **Headers:** `Authorization: Bearer <token>`
    *   **Request Body:**
        ```json
        {
            "mentor": 2,  // User ID of the mentor
            "message": "I would like guidance on my Django project"
        }
        ```

*   **Student: List My Requests**
    *   **Method:** `GET`
    *   **Endpoint:** `/api/users/api/mentorship-requests/student/`
    *   **Headers:** `Authorization: Bearer <token>`

*   **Mentor: List Received Requests**
    *   **Method:** `GET`
    *   **Endpoint:** `/api/users/api/mentorship-requests/mentor/`
    *   **Headers:** `Authorization: Bearer <token>`

*   **Mentor: Accept Request**
    *   **Method:** `PATCH`
    *   **Endpoint:** `/api/users/api/mentorship-requests/<id>/accept/`
    *   **Headers:** `Authorization: Bearer <token>`

*   **Mentor: Decline Request**
    *   **Method:** `PATCH`
    *   **Endpoint:** `/api/users/api/mentorship-requests/<id>/decline/`
    *   **Headers:** `Authorization: Bearer <token>`
    *   **Request Body:**
        ```json
        {
            "rejection_reason": "I'm currently at full capacity with mentees"
        }
        ```

## Messaging System

### Send Message

*   **Method:** `POST`
*   **Endpoint:** `/api/users/messages/`
*   **Headers:** 
    * `Authorization: Bearer <token>`
    * `Content-Type: multipart/form-data` (for file uploads)
*   **Request Body:**
    ```json
    {
        "receiver": 2,  // User ID of the recipient
        "content": "Hello, can you help me with my project?",
        "file": "[file upload]"  // Optional
    }
    ```
*   **Sample Success Response (201 Created):**
    ```json
    {
        "id": 1,
        "sender": 1,
        "receiver": 2,
        "sender_username": "student1",
        "receiver_username": "mentor1",
        "content": "Hello, can you help me with my project?",
        "file_url": "/media/message_files/document.pdf",
        "timestamp": "2023-06-02T14:35:22Z"
    }
    ```

### Get Message History

*   **Method:** `GET`
*   **Endpoint:** `/api/users/messages/<user_id>/`
*   **Headers:** `Authorization: Bearer <token>`
*   **Sample Success Response (200 OK):**
    ```json
    [
        {
            "id": 1,
            "sender": 1,
            "receiver": 2,
            "sender_username": "student1",
            "receiver_username": "mentor1",
            "content": "Hello, can you help me with my project?",
            "file_url": "/media/message_files/document.pdf",
            "timestamp": "2023-06-02T14:35:22Z"
        },
        {
            "id": 2,
            "sender": 2,
            "receiver": 1,
            "sender_username": "mentor1",
            "receiver_username": "student1",
            "content": "Yes, I'd be happy to help. What's the project about?",
            "file_url": null,
            "timestamp": "2023-06-02T14:40:15Z"
        }
    ]
    ```

### Real-time Message Stream

*   **Method:** `GET`
*   **Endpoint:** `/api/users/messages/stream/<user_id>/`
*   **Headers:** `Authorization: Bearer <token>`
*   **Description:** Establishes an event stream connection for real-time message updates.

## Protected Example Route

*   **Method:** `GET`
*   **Endpoint:** `/api/users/protected/`
*   **Headers:** `Authorization: Bearer <token>`
*   **Response (200 OK):**
    ```json
    {
        "message": "Hello, yourusername! This is protected content."
    }
    ```

## File Upload Validation

The API implements strict validation for all file uploads:

### Profile Photos
- Maximum size: 2MB
- Allowed formats: JPEG, PNG, WebP
- Automatically cropped to 1:1 aspect ratio

### Message Attachments
- Maximum size: 5MB
- Allowed formats: PDF, DOCX, XLSX, PPTX, TXT, CSV, PNG, JPEG, GIF

## Testing Rate Limiting

To test the rate limiting functionality:

1. Send multiple requests to a rate-limited endpoint in quick succession
2. After exceeding the rate limit (e.g., 5 requests in 1 minute for registration), you'll receive a 429 response
3. The response will indicate how many seconds to wait before trying again

Example using curl:
```bash
# Send multiple registration requests quickly
for i in {1..6}; do
  curl -X POST http://localhost:8000/api/users/api/register/ \
    -H "Content-Type: application/json" \
    -d '{"username":"test'$i'", "password":"test123", "password2":"test123", "email":"test'$i'@example.com", "user_type": "student", "name": "Test User '$i'"}'
  echo -e "\n"
  sleep 1
done
```
```