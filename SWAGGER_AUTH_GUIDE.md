# Swagger UI Authentication Guide

This guide explains how to properly authenticate in Swagger UI using JWT tokens for the DevGuidance API.

## Step-by-Step Authentication Process

### 1. Obtain JWT Token

First, get your JWT access token by calling the login endpoint:

**Endpoint:** `POST /api/token/`

**Request Body:**
```json
{
    "username": "your_username",
    "password": "your_password"
}
```

**Response:**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

Copy the `access` token value.

### 2. Authenticate in Swagger UI

1. **Open Swagger UI** at: `http://127.0.0.1:8000/swagger/` (local) or your production URL

2. **Click the "Authorize" button** (🔒 icon) at the top right of the Swagger UI

3. **In the Authorization popup:**
   - You'll see a field labeled "Bearer (apiKey)"
   - **Enter:** `Bearer your_access_token_here`
   - **Example:** `Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...`

4. **Click "Authorize"**

5. **Click "Close"**

### 3. Test Protected Endpoints

Now you can test any protected endpoint. The JWT token will be automatically included in the Authorization header.

## ⚠️ Common Issues and Solutions

### Issue 1: "Authentication credentials were not provided"

**Cause:** Token not properly formatted or not included

**Solution:** 
- Ensure you include the word "Bearer" before your token
- Format: `Bearer your_token_here` (note the space)
- ❌ Wrong: `eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...`
- ✅ Correct: `Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...`

### Issue 2: Token appears to be set but still getting auth errors

**Solution:**
1. Click "Authorize" again and clear the field
2. Re-enter the token with "Bearer " prefix
3. Make sure there are no extra spaces or characters
4. Refresh the page and try again

### Issue 3: Token expired

**Cause:** JWT tokens have expiration times (default: 60 minutes)

**Solution:**
1. Get a new token using `POST /api/token/`
2. Or use the refresh token: `POST /api/token/refresh/`
3. Update the authorization in Swagger UI

## Testing Different User Types

### For Students:
```json
{
    "username": "student_user",
    "password": "your_password"
}
```

### For Mentors:
```json
{
    "username": "mentor_user", 
    "password": "your_password"
}
```

## Postman vs Swagger UI

### Postman (What works for you):
- Header: `Authorization: Bearer your_token`
- This works because you manually set the header

### Swagger UI (Updated configuration):
- Uses the same format internally
- The "Authorize" button sets the header automatically
- Should now work the same as Postman

## API Endpoints That Require Authentication

- `GET /api/users/students/profiles/me/` - Get your student profile
- `GET /api/users/mentors/profiles/me/` - Get your mentor profile
- `POST /api/users/mentorship-requests/` - Create mentorship request
- `GET /api/users/messages/{user_id}/` - Get messages
- `POST /api/users/messages/` - Send message

## Troubleshooting Checklist

1. ✅ Token obtained from `/api/token/` endpoint
2. ✅ Token includes "Bearer " prefix in Swagger UI
3. ✅ No extra spaces or characters
4. ✅ Token not expired (check timestamp)
5. ✅ User has proper permissions for the endpoint
6. ✅ Page refreshed after authorization

## Example: Complete Flow

1. **Get Token:**
   ```bash
   curl -X POST http://127.0.0.1:8000/api/token/ \
     -H "Content-Type: application/json" \
     -d '{"username": "testuser", "password": "testpass123"}'
   ```

2. **Response:**
   ```json
   {"access": "eyJ0eXAiOiJKV1Q..."}
   ```

3. **In Swagger UI Authorize field:**
   ```
   Bearer eyJ0eXAiOiJKV1Q...
   ```

4. **Test protected endpoint** - should work now!

## Need Help?

If you're still having issues:
1. Check the browser's developer console for error messages
2. Verify the token format matches exactly: `Bearer <space> <token>`
3. Try the same request in Postman to confirm the token works
4. Check that the user account has the right permissions

The updated configuration should resolve the authentication issues in Swagger UI! 