# DevGuidance API Documentation

## Authentication

### Register User

*   **Method:** `POST`
*   **Endpoint:** `/api/users/register/`
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
            "tech_stack": []
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
            "name": "Student Name",
            "bio": "Student bio",
            "year_level": 2,
            "tech_stack": ["Python", "Django", "React"]
        }
        ```

*   **Update Profile**
    *   **Method:** `PUT/PATCH`
    *   **Endpoint:** `/api/users/api/student-profiles/<id>/`
    *   **Headers:** `Authorization: Bearer <token>`
    *   **Request Body:**
        ```json
        {
            "name": "Updated Name",
            "bio": "New bio",
            "year_level": 3,
            "tech_stack": ["Python", "Django", "React", "NextJS"]
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
    *   **Headers:** `Authorization: Bearer <token>`
    *   **Request Body:**
        ```json
        {
            "name": "Mentor Name",
            "bio": "Mentor bio",
            "experience_years": 5,
            "expertise_tags": ["Python", "Django", "Machine Learning"]
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
*   **Headers:** `Authorization: Bearer <token>`
*   **Request Body:**
    ```json
    {
        "receiver": 2,  // User ID of the recipient
        "content": "Hello, can you help me with my project?"
    }
    ```
*   **Sample Success Response (201 Created):**
    ```json
    {
        "id": 1,
        "sender": 1,
        "receiver": 2,
        "content": "Hello, can you help me with my project?",
        "file_url": null,
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
            "content": "Hello, can you help me with my project?",
            "file_url": null,
            "timestamp": "2023-06-02T14:35:22Z"
        },
        {
            "id": 2,
            "sender": 2,
            "receiver": 1,
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
