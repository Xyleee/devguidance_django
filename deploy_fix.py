#!/usr/bin/env python3
"""
Deployment script to fix the registration error
Run this script to apply all necessary fixes
"""

import os
import sys
import subprocess

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}")
    print(f"Running: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True)
        print(f"✅ Success: {description}")
        if result.stdout:
            print(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {description}")
        print(f"Error output: {e.stderr}")
        return False

def main():
    print("🚀 DevGuidance Registration Fix Deployment")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('manage.py'):
        print("❌ Error: Please run this script from the Django project directory")
        print("Expected to find manage.py in current directory")
        return False
    
    # Step 1: Try to run migrations with the original settings
    print("\n📝 Step 1: Attempting to run migrations with original settings")
    success = run_command(
        "python manage.py migrate users",
        "Running migration with original settings"
    )
    
    # Step 2: If that fails, try with local settings
    if not success:
        print("\n📝 Step 2: Trying with local settings (fallback)")
        success = run_command(
            "python manage.py migrate users --settings=devguidance_django.local_settings",
            "Running migration with local settings"
        )
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("\n📋 Next Steps:")
        print("1. Deploy your updated code to your hosting platform")
        print("2. Make sure the migration runs on your production database")
        print("3. Test registration with the test_registration.py script")
        print("\n🔧 Test your registration endpoint:")
        print("   python test_registration.py")
        
        return True
    else:
        print("\n❌ Migration failed!")
        print("\n🔧 Manual steps required:")
        print("1. Check your virtual environment setup")
        print("2. Install missing dependencies:")
        print("   pip install python-decouple django djangorestframework")
        print("3. Try running the migration manually")
        print("\n📖 See REGISTRATION_FIX.md for detailed troubleshooting")
        
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 