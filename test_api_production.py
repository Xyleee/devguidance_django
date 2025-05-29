#!/usr/bin/env python
"""
Production API Test Script
Test the deployed API endpoints to verify everything works correctly.
"""
import requests
import json
import time

# Your production API base URL (update this with your actual URL)
BASE_URL = "https://devguidance-django.onrender.com/api"

def test_api_connectivity():
    """Test basic API connectivity"""
    print("🔗 Testing API connectivity...")
    
    try:
        response = requests.get(f"{BASE_URL}/users/simple/", timeout=10)
        if response.status_code == 200:
            print("✅ API is accessible")
            return True
        else:
            print(f"❌ API returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API connectivity failed: {e}")
        return False

def test_registration():
    """Test user registration"""
    print("\n📝 Testing user registration...")
    
    # Test data
    test_data = {
        "username": f"testuser_{int(time.time())}",  # Unique username
        "email": f"test_{int(time.time())}@example.com",  # Unique email
        "password": "testpass123",
        "password2": "testpass123",
        "user_type": "student",
        "name": "Test User",
        "first_name": "Test",
        "last_name": "User"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/users/register/", 
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 201:
            print("✅ Registration successful!")
            data = response.json()
            print(f"   User ID: {data.get('user', {}).get('id')}")
            print(f"   Username: {data.get('user', {}).get('username')}")
            print(f"   Access Token: {'✓' if data.get('access') else '✗'}")
            return True
        else:
            print(f"❌ Registration failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Registration request failed: {e}")
        return False

def test_cors():
    """Test CORS headers"""
    print("\n🌐 Testing CORS configuration...")
    
    try:
        # Make an OPTIONS request to check CORS
        response = requests.options(
            f"{BASE_URL}/users/register/",
            headers={
                'Origin': 'https://example.com',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type,Authorization'
            },
            timeout=10
        )
        
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
        }
        
        print("CORS Headers:")
        for header, value in cors_headers.items():
            status = "✅" if value else "❌"
            print(f"   {status} {header}: {value or 'Not present'}")
            
        return any(cors_headers.values())
        
    except Exception as e:
        print(f"❌ CORS test failed: {e}")
        return False

def test_api_docs():
    """Test API documentation accessibility"""
    print("\n📚 Testing API documentation...")
    
    try:
        # Test schema endpoint
        response = requests.get(f"{BASE_URL}/schema/", timeout=10)
        if response.status_code == 200:
            print("✅ API schema accessible")
            schema_size = len(response.content)
            print(f"   Schema size: {schema_size} bytes")
        else:
            print(f"❌ API schema failed: {response.status_code}")
            
        # Test docs endpoint (if available)
        try:
            docs_response = requests.get(f"{BASE_URL}/docs/", timeout=10)
            if docs_response.status_code == 200:
                print("✅ API docs accessible")
            else:
                print(f"⚠️  API docs not accessible: {docs_response.status_code}")
        except:
            print("⚠️  API docs endpoint not found")
            
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ API docs test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("🚀 PRODUCTION API TESTING")
    print("=" * 60)
    print(f"Testing API at: {BASE_URL}")
    print()
    
    results = []
    
    # Run tests
    results.append(("API Connectivity", test_api_connectivity()))
    results.append(("CORS Configuration", test_cors()))
    results.append(("API Documentation", test_api_docs()))
    results.append(("User Registration", test_registration()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
    
    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)
    
    print(f"\nOverall: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("🎉 All tests passed! Your API is working correctly.")
    elif total_passed >= total_tests * 0.75:
        print("⚠️  Most tests passed. Check failed tests above.")
    else:
        print("❌ Multiple test failures. Please check your deployment.")
    
    print("=" * 60)

if __name__ == "__main__":
    main() 