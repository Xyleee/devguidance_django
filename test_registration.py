#!/usr/bin/env python3
"""
Test script to debug registration issues
"""
import requests
import json

# Your backend URL - update this to your hosted backend URL
BASE_URL = "https://your-backend-url.com"  # Replace with actual URL

def test_registration():
    url = f"{BASE_URL}/users/api/register/"
    
    # Test data for student registration
    student_data = {
        "username": "teststudent123",
        "email": "test@example.com",
        "password": "TestPassword123!",
        "password2": "TestPassword123!",
        "user_type": "student",
        "name": "Test Student",
        "first_name": "Test",
        "last_name": "Student"
    }
    
    try:
        print(f"Testing registration at: {url}")
        print(f"Data: {json.dumps(student_data, indent=2)}")
        
        response = requests.post(url, json=student_data)
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            print(f"Response: {json.dumps(response_data, indent=2)}")
        except:
            print(f"Raw Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Replace with your actual backend URL
    print("Enter your backend URL (e.g., https://your-backend.vercel.app):")
    backend_url = input().strip()
    if backend_url:
        BASE_URL = backend_url
    
    test_registration() 