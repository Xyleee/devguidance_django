#!/usr/bin/env python
"""
Test script to verify the registration fix works correctly.
This script tests if the corrected related_name attributes resolve the 500 error.
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'devguidance_django.settings')

# Setup Django
django.setup()

from django.contrib.auth.models import User
from users.models import StudentProfile, MentorProfile

def test_user_profile_relationships():
    """Test if user profile relationships work correctly"""
    
    print("Testing user profile relationships...")
    
    # Test 1: Create a student user and profile
    try:
        # Create test student user
        student_user = User.objects.create_user(
            username='test_student',
            email='student@test.com',
            password='testpass123'
        )
        
        # Create student profile
        student_profile = StudentProfile.objects.create(
            user=student_user,
            name='Test Student'
        )
        
        # Test accessing the profile via the related name
        accessed_profile = student_user.student_profile
        print(f"✓ Student profile access works: {accessed_profile.name}")
        
        # Clean up
        student_user.delete()
        
    except Exception as e:
        print(f"✗ Student profile test failed: {e}")
        return False
    
    # Test 2: Create a mentor user and profile
    try:
        # Create test mentor user
        mentor_user = User.objects.create_user(
            username='test_mentor',
            email='mentor@test.com',
            password='testpass123'
        )
        
        # Create mentor profile
        mentor_profile = MentorProfile.objects.create(
            user=mentor_user,
            name='Test Mentor'
        )
        
        # Test accessing the profile via the related name
        accessed_profile = mentor_user.mentor_profile
        print(f"✓ Mentor profile access works: {accessed_profile.name}")
        
        # Clean up
        mentor_user.delete()
        
    except Exception as e:
        print(f"✗ Mentor profile test failed: {e}")
        return False
    
    print("✓ All profile relationship tests passed!")
    return True

def test_registration_serializer():
    """Test if the registration serializer works without errors"""
    
    print("\nTesting registration serializer...")
    
    from users.serializers import RegisterSerializer
    
    # Test student registration data
    student_data = {
        'username': 'teststudent2',
        'email': 'student2@test.com',
        'password': 'testpass123',
        'password2': 'testpass123',
        'user_type': 'student',
        'name': 'Test Student 2'
    }
    
    try:
        serializer = RegisterSerializer(data=student_data)
        if serializer.is_valid():
            user = serializer.save()
            print(f"✓ Student registration serializer works: {user.username}")
            
            # Test profile access
            profile = user.student_profile
            print(f"✓ Student profile accessible: {profile.name}")
            
            # Clean up
            user.delete()
        else:
            print(f"✗ Student serializer validation failed: {serializer.errors}")
            return False
            
    except Exception as e:
        print(f"✗ Student registration test failed: {e}")
        return False
    
    # Test mentor registration data
    mentor_data = {
        'username': 'testmentor2',
        'email': 'mentor2@test.com',
        'password': 'testpass123',
        'password2': 'testpass123',
        'user_type': 'mentor',
        'name': 'Test Mentor 2'
    }
    
    try:
        serializer = RegisterSerializer(data=mentor_data)
        if serializer.is_valid():
            user = serializer.save()
            print(f"✓ Mentor registration serializer works: {user.username}")
            
            # Test profile access
            profile = user.mentor_profile
            print(f"✓ Mentor profile accessible: {profile.name}")
            
            # Clean up
            user.delete()
        else:
            print(f"✗ Mentor serializer validation failed: {serializer.errors}")
            return False
            
    except Exception as e:
        print(f"✗ Mentor registration test failed: {e}")
        return False
    
    print("✓ All serializer tests passed!")
    return True

if __name__ == '__main__':
    print("=" * 50)
    print("TESTING REGISTRATION FIX")
    print("=" * 50)
    
    success = True
    success &= test_user_profile_relationships()
    success &= test_registration_serializer()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 ALL TESTS PASSED! The registration fix should work.")
    else:
        print("❌ SOME TESTS FAILED. There may still be issues.")
    print("=" * 50) 