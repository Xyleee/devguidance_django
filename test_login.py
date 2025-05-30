#!/usr/bin/env python
"""
Simple test script to verify login authentication response format.
This script can be run to check if the login endpoint returns clean responses.
"""

import os
import sys
import django
from django.conf import settings

# Setup Django environment
sys.path.append(os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'devguidance_django.settings')
django.setup()

from rest_framework.test import APIClient
from django.contrib.auth.models import User
from students.models import StudentProfile
from mentors.models import MentorProfile
import json

def test_clean_login_response():
    """Test that login endpoint returns clean response format"""
    client = APIClient()
    
    # Create test student user
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpassword123'
    )
    
    # Create student profile
    StudentProfile.objects.create(
        user=user,
        name='Test User',
        bio='Test bio',
        year_level=2,
        tech_stack=['Python', 'Django']
    )
    
    # Test login
    data = {
        'username': 'testuser',
        'password': 'testpassword123'
    }
    
    response = client.post('/api/token/', data)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Data: {json.dumps(response.data, indent=2)}")
    
    # Check expected structure
    expected_keys = {'message', 'user', 'tokens'}
    actual_keys = set(response.data.keys())
    
    if actual_keys == expected_keys:
        print("✅ Response structure is clean - contains only 'message', 'user', and 'tokens'")
    else:
        print(f"❌ Response structure issue. Expected: {expected_keys}, Got: {actual_keys}")
    
    if response.data.get('message') == 'Login successful':
        print("✅ Success message is correct")
    else:
        print(f"❌ Success message issue. Got: {response.data.get('message')}")
    
    # Test mentor user
    mentor_user = User.objects.create_user(
        username='mentoruser',
        email='mentor@example.com',
        password='mentorpassword123'
    )
    
    MentorProfile.objects.create(
        user=mentor_user,
        name='Mentor User',
        bio='Senior Developer',
        years_of_experience=5,
        expertise_tags=['Python', 'Django', 'AWS'],
        company='Tech Corp',
        position='Senior Developer'
    )
    
    # Test mentor login
    mentor_data = {
        'username': 'mentoruser',
        'password': 'mentorpassword123'
    }
    
    mentor_response = client.post('/api/token/', mentor_data)
    
    print(f"\nMentor Status Code: {mentor_response.status_code}")
    print(f"Mentor Response Data: {json.dumps(mentor_response.data, indent=2)}")
    
    mentor_actual_keys = set(mentor_response.data.keys())
    
    if mentor_actual_keys == expected_keys:
        print("✅ Mentor response structure is clean")
    else:
        print(f"❌ Mentor response structure issue. Expected: {expected_keys}, Got: {mentor_actual_keys}")
    
    # Clean up
    user.delete()
    mentor_user.delete()

if __name__ == '__main__':
    test_clean_login_response() 