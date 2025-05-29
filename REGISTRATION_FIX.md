# Registration Error Fix

## Problem Identified

The 500 and 400 errors during registration were caused by **conflicting Django model relationships**:

### Conflicting Models

1. **`users/models.py`** had:
   - `StudentProfile` with `related_name='student_profile'` (singular)
   - `MentorProfile` with `related_name='mentor_profile'` (singular)

2. **`students/models.py`** had:
   - `StudentProfile` with `related_name='students_profile'` (plural)

3. **`mentors/models.py`** had:
   - `MentorProfile` with `related_name='mentors_profile'` (plural)

This created multiple OneToOneField relationships to the same User model with different `related_name` values, causing Django to fail when trying to access the profile relationships.

### Error in RegisterView

The `RegisterView.create()` method was trying to access:
```python
profile = user.students_profile  # This would fail
profile = user.mentors_profile   # This would fail
```

But the models in the users app used singular names (`student_profile`, `mentor_profile`).

## Solution Implemented

### 1. Removed Duplicate Models

Removed the conflicting models from `users/models.py`:
- `StudentProfile` 
- `MentorProfile`
- `StudentProject`
- `MentorshipRequest`

Kept only the `Message` model which is unique to the users app.

### 2. Updated Imports

Updated `users/serializers.py` and `users/views.py` to import the correct models:
```python
from students.models import StudentProfile, StudentProject
from mentors.models import MentorProfile, MentorshipRequest
```

### 3. Fixed Serializers

Updated serializers to use the correct field names:
- `profile_picture` instead of `photo`
- Correct relationship names (`students_profile`, `mentors_profile`)

### 4. Migration Required

Created migration `users/migrations/0006_remove_duplicate_models.py` to remove the duplicate models from the database.

## Virtual Environment Issues

### Decouple Dependency Error

If you encounter the error:
```
ModuleNotFoundError: No module named 'decouple'
```

This means the `python-decouple` package is not installed in your virtual environment.

### Solutions:

#### Option 1: Install decouple (Recommended)
```bash
# Activate your virtual environment first
# On Windows:
Scripts\activate.bat

# Then install the package
pip install python-decouple
```

#### Option 2: Use Local Settings (For testing only)
If you can't install packages, I've created `devguidance_django/local_settings.py` that doesn't require decouple. Use it for local testing:

```bash
python manage.py makemigrations users --settings=devguidance_django.local_settings
python manage.py migrate users --settings=devguidance_django.local_settings
```

**Note**: Only use local_settings for development. Your production environment should use the original settings with proper environment variables.

## Steps to Deploy the Fix

### 1. Apply the Code Changes
All code changes have been made to:
- `users/models.py` - Removed duplicate models
- `users/serializers.py` - Updated imports and field names
- `users/views.py` - Updated imports

### 2. Fix Virtual Environment (If needed)

If you have virtual environment issues:

```bash
# Make sure you're in the right directory
cd C:\Users\james\OneDrive\Documents\GitHub\layugan_activities_BSIT3C\pyenv

# Activate virtual environment
Scripts\activate.bat

# Install missing dependencies
pip install python-decouple
pip install django
pip install djangorestframework
pip install python-magic
pip install Pillow
```

### 3. Create and Apply Migration

**For production (with proper virtual environment):**
```bash
python manage.py makemigrations users
python manage.py migrate users
```

**For local testing (if virtual environment has issues):**
```bash
python manage.py makemigrations users --settings=devguidance_django.local_settings
python manage.py migrate users --settings=devguidance_django.local_settings
```

### 4. Test Registration

Use the provided `test_registration.py` script to test the fixed registration endpoint:

```bash
python test_registration.py
```

## Expected Behavior After Fix

1. **Registration should work** for both students and mentors
2. **Profile creation** should use the correct models from students/mentors apps
3. **JWT tokens** should be generated properly
4. **No more 500 errors** from conflicting model relationships

## Additional Notes

### Database Considerations

- The existing data in the duplicate tables will be lost when applying the migration
- If you have important data, back it up before running the migration
- The students and mentors apps have their own profile tables that should be used instead

### Testing

After deployment:
1. Test student registration
2. Test mentor registration  
3. Test profile creation and retrieval
4. Verify JWT token generation

### Dependencies

Make sure these packages are installed in your environment:
- `python-decouple` (for environment variable management)
- `python-magic` (for file validation)
- `Pillow` (for image processing)
- `django`
- `djangorestframework`
- `djangorestframework-simplejwt`
- All other requirements from `requirements.txt`

## Troubleshooting

### Virtual Environment Issues

If your virtual environment is corrupted or missing packages:

1. **Recreate the virtual environment:**
   ```bash
   cd C:\Users\james\OneDrive\Documents\GitHub\layugan_activities_BSIT3C\pyenv
   deactivate  # if currently activated
   cd ..
   python -m venv pyenv  # recreate
   cd pyenv
   Scripts\activate.bat
   pip install -r devguidance_django/requirements.txt
   ```

2. **Check Python installation:**
   ```bash
   where python
   python --version
   ```

### After Migration Issues

If you still get errors after applying this fix:

1. **Check migration status**: `python manage.py showmigrations`
2. **Check database tables**: Ensure duplicate tables are removed
3. **Check imports**: Verify all model imports are correct
4. **Check logs**: Look at Django server logs for specific error messages

The registration should work properly once these conflicting models are resolved and the virtual environment is properly set up. 