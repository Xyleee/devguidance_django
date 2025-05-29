#!/usr/bin/env python3
"""
Test script for DevGuidance API deployment
Run this to verify your API is working correctly
"""

import requests
import json
from datetime import datetime

# Replace with your actual Render URL
BASE_URL = "https://your-service-name.onrender.com"

def test_api():
    print("🧪 Testing DevGuidance API Deployment")
    print("=" * 50)
    
    # Test 1: API Health Check
    print("\n1. Testing API Health...")
    try:
        response = requests.get(f"{BASE_URL}/api/docs/")
        if response.status_code == 200:
            print("✅ API is accessible")
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        return
    
    # Test 2: User Registration
    print("\n2. Testing User Registration...")
    test_user = {
        "username": f"testuser_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "email": f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com",
        "password": "testpass123",
        "password2": "testpass123",
        "user_type": "student",
        "name": "Test User"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/users/api/register/",
            headers={"Content-Type": "application/json"},
            data=json.dumps(test_user)
        )
        
        if response.status_code == 201:
            print("✅ User registration successful")
            user_data = response.json()
            print(f"   Created user: {user_data.get('user', {}).get('username')}")
        else:
            print(f"❌ Registration failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return
    
    # Test 3: Token Authentication
    print("\n3. Testing Authentication...")
    login_data = {
        "username": test_user["username"],
        "password": test_user["password"]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/token/",
            headers={"Content-Type": "application/json"},
            data=json.dumps(login_data)
        )
        
        if response.status_code == 200:
            print("✅ Authentication successful")
            tokens = response.json()
            access_token = tokens.get("access")
            print(f"   Got access token: {access_token[:50]}...")
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return
    
    # Test 4: Protected Endpoint
    print("\n4. Testing Protected Endpoint...")
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            f"{BASE_URL}/api/users/api/student-profiles/me/",
            headers=headers
        )
        
        if response.status_code == 200:
            print("✅ Protected endpoint accessible")
            profile_data = response.json()
            print(f"   Profile name: {profile_data.get('name')}")
        else:
            print(f"❌ Protected endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Protected endpoint error: {e}")
    
    # Test 5: Create Student Project
    print("\n5. Testing Student Project Creation...")
    project_data = {
        "title": "Test Project",
        "description": "A test project created via API",
        "tools_used": ["Python", "Django", "PostgreSQL"]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/users/api/student-projects/",
            headers=headers,
            data=json.dumps(project_data)
        )
        
        if response.status_code == 201:
            print("✅ Project creation successful")
            project = response.json()
            print(f"   Created project: {project.get('title')}")
        else:
            print(f"❌ Project creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Project creation error: {e}")
    
    # Test 6: List Student Projects
    print("\n6. Testing Project Listing...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/users/api/student-projects/",
            headers=headers
        )
        
        if response.status_code == 200:
            print("✅ Project listing successful")
            projects = response.json()
            print(f"   Found {len(projects)} projects")
        else:
            print(f"❌ Project listing failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Project listing error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 API Testing Complete!")
    print(f"\n📋 Test Summary:")
    print(f"   Base URL: {BASE_URL}")
    print(f"   Swagger UI: {BASE_URL}/api/docs/")
    print(f"   ReDoc: {BASE_URL}/api/redoc/")
    print(f"   Admin Panel: {BASE_URL}/admin/")

if __name__ == "__main__":
    # Update this with your actual Render URL
    BASE_URL = input("Enter your Render URL (e.g., https://devguidance-api.onrender.com): ").strip()
    if not BASE_URL.startswith('http'):
        BASE_URL = f"https://{BASE_URL}"
    
    test_api() 