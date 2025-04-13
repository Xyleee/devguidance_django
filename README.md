# Project API Documentation

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
        "password2": "password",
        "first_name": "Test", // Optional
        "last_name": "User"   // Optional
    }
    ```
*   **Sample Success Response (201 Created):**
    ```json
    {
        "username": "newuser",
        "email": "user@example.com",
        "first_name": "Test",
        "last_name": "User"
    }
    ```
*   **Sample Error Response (400 Bad Request):**
    ```json
    {
        "password": [
            "Password fields didn't match."
        ]
        // Or other validation errors like:
        // "username": ["A user with that username already exists."]
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
        "username": "yourusername",
        "password": "yourpassword"
    }
    ```
*   **Sample Success Response (200 OK):**
    ```json
    {
        "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    ```
*   **Sample Error Response (401 Unauthorized):**
    ```json
    {
        "detail": "No active account found with the given credentials"
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
        // May include refresh token if ROTATE_REFRESH_TOKENS=True
    }
    ```
*   **Sample Error Response (401 Unauthorized):**
    ```json
    {
        "detail": "Token is invalid or expired",
        "code": "token_not_valid"
    }
    ```

## Protected Routes

### Example Protected Route

*   **Method:** `GET`
*   **Endpoint:** `/api/users/protected/`
*   **Headers:**
    *   `Authorization: Bearer <your_access_token>`
*   **Request Body:** None
*   **Sample Success Response (200 OK):**
    ```json
    {
        "message": "Hello, yourusername! This is protected content."
    }
    ```
*   **Sample Error Response (401 Unauthorized):**
    ```json
    {
        "detail": "Authentication credentials were not provided."
        // Or token validation errors
    }
    ```
