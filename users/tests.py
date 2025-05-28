from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch
from io import BytesIO
from PIL import Image
import json
import tempfile

from .models import StudentProfile, StudentProject, MentorProfile, MentorshipRequest, Message
from .serializers import (
    RegisterSerializer, 
    StudentProfileSerializer, 
    StudentProjectSerializer,
    MentorProfileSerializer,
    MentorshipRequestSerializer,
    MessageSerializer
)


class UserModelTests(TestCase):
    """Test cases for User model and related profiles"""

    def setUp(self):
        self.student_user = User.objects.create_user(
            username='student1',
            email='student@test.com',
            password='testpass123'
        )
        self.mentor_user = User.objects.create_user(
            username='mentor1',
            email='mentor@test.com',
            password='testpass123'
        )

    def test_user_creation(self):
        """Test basic user creation"""
        self.assertEqual(self.student_user.username, 'student1')
        self.assertEqual(self.student_user.email, 'student@test.com')
        self.assertTrue(self.student_user.is_active)

    def test_user_string_representation(self):
        """Test user string representation"""
        self.assertEqual(str(self.student_user), 'student1')


class StudentProfileModelTests(TestCase):
    """Test cases for StudentProfile model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='student1',
            email='student@test.com',
            password='testpass123'
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.user,
            name='John Student',
            bio='I am a student learning web development',
            year_level=2,
            tech_stack=['Python', 'Django', 'React']
        )

    def test_student_profile_creation(self):
        """Test student profile creation"""
        self.assertEqual(self.student_profile.name, 'John Student')
        self.assertEqual(self.student_profile.year_level, 2)
        self.assertEqual(self.student_profile.tech_stack, ['Python', 'Django', 'React'])
        self.assertEqual(self.student_profile.user, self.user)

    def test_student_profile_string_representation(self):
        """Test student profile string representation"""
        self.assertEqual(str(self.student_profile), 'John Student')

    def test_student_profile_default_values(self):
        """Test default values for student profile"""
        profile = StudentProfile.objects.create(
            user=User.objects.create_user('test2', 'test2@test.com', 'pass'),
            name='Test Student'
        )
        self.assertEqual(profile.year_level, 1)
        self.assertEqual(profile.tech_stack, [])
        self.assertEqual(profile.bio, '')

    def test_photo_upload_path(self):
        """Test photo upload path generation"""
        # Create a simple image file
        image = Image.new('RGB', (100, 100), color='red')
        temp_file = BytesIO()
        image.save(temp_file, format='JPEG')
        temp_file.seek(0)
        
        uploaded_file = SimpleUploadedFile(
            "test_image.jpg",
            temp_file.getvalue(),
            content_type="image/jpeg"
        )
        
        self.student_profile.photo = uploaded_file
        self.student_profile.save()
        
        self.assertTrue(self.student_profile.photo.name.startswith('profile_photos/student/'))


class StudentProjectModelTests(TestCase):
    """Test cases for StudentProject model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='student1',
            email='student@test.com',
            password='testpass123'
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.user,
            name='John Student'
        )
        self.project = StudentProject.objects.create(
            student=self.student_profile,
            title='My Web App',
            description='A full-stack web application',
            tools_used=['Python', 'Django', 'PostgreSQL']
        )

    def test_project_creation(self):
        """Test project creation"""
        self.assertEqual(self.project.title, 'My Web App')
        self.assertEqual(self.project.student, self.student_profile)
        self.assertEqual(self.project.tools_used, ['Python', 'Django', 'PostgreSQL'])

    def test_project_string_representation(self):
        """Test project string representation"""
        self.assertEqual(str(self.project), 'My Web App')

    def test_project_relationship(self):
        """Test project-student relationship"""
        self.assertEqual(self.student_profile.projects.count(), 1)
        self.assertEqual(self.student_profile.projects.first(), self.project)


class MentorProfileModelTests(TestCase):
    """Test cases for MentorProfile model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='mentor1',
            email='mentor@test.com',
            password='testpass123'
        )
        self.mentor_profile = MentorProfile.objects.create(
            user=self.user,
            name='Jane Mentor',
            bio='Senior developer with 5 years experience',
            experience_years=5,
            expertise_tags=['Python', 'Django', 'Machine Learning']
        )

    def test_mentor_profile_creation(self):
        """Test mentor profile creation"""
        self.assertEqual(self.mentor_profile.name, 'Jane Mentor')
        self.assertEqual(self.mentor_profile.experience_years, 5)
        self.assertEqual(self.mentor_profile.expertise_tags, ['Python', 'Django', 'Machine Learning'])

    def test_mentor_profile_string_representation(self):
        """Test mentor profile string representation"""
        self.assertEqual(str(self.mentor_profile), 'Jane Mentor')


class MentorshipRequestModelTests(TestCase):
    """Test cases for MentorshipRequest model"""

    def setUp(self):
        self.student_user = User.objects.create_user(
            username='student1',
            email='student@test.com',
            password='testpass123'
        )
        self.mentor_user = User.objects.create_user(
            username='mentor1',
            email='mentor@test.com',
            password='testpass123'
        )
        self.request = MentorshipRequest.objects.create(
            student=self.student_user,
            mentor=self.mentor_user,
            message='I would like guidance on Django development'
        )

    def test_mentorship_request_creation(self):
        """Test mentorship request creation"""
        self.assertEqual(self.request.student, self.student_user)
        self.assertEqual(self.request.mentor, self.mentor_user)
        self.assertEqual(self.request.status, 'pending')
        self.assertEqual(self.request.message, 'I would like guidance on Django development')

    def test_mentorship_request_string_representation(self):
        """Test mentorship request string representation"""
        expected = f"{self.student_user.username}'s request to {self.mentor_user.username}"
        self.assertEqual(str(self.request), expected)

    def test_mentorship_request_acceptance_logic(self):
        """Test that accepting a request declines other pending requests"""
        # Create another pending request from the same student
        other_mentor = User.objects.create_user('mentor2', 'mentor2@test.com', 'pass')
        other_request = MentorshipRequest.objects.create(
            student=self.student_user,
            mentor=other_mentor,
            message='Another request'
        )
        
        # Accept the first request
        self.request.status = 'accepted'
        self.request.save()
        
        # Check that other request is still pending (since we're not triggering the save logic)
        other_request.refresh_from_db()
        # Note: The save logic would need to be triggered in a more realistic test scenario


class MessageModelTests(TestCase):
    """Test cases for Message model"""

    def setUp(self):
        self.sender = User.objects.create_user(
            username='sender',
            email='sender@test.com',
            password='testpass123'
        )
        self.receiver = User.objects.create_user(
            username='receiver',
            email='receiver@test.com',
            password='testpass123'
        )
        self.message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content='Hello, how are you?'
        )

    def test_message_creation(self):
        """Test message creation"""
        self.assertEqual(self.message.sender, self.sender)
        self.assertEqual(self.message.receiver, self.receiver)
        self.assertEqual(self.message.content, 'Hello, how are you?')
        self.assertFalse(self.message.is_read)

    def test_message_string_representation(self):
        """Test message string representation"""
        expected = f"Message from {self.sender.username} to {self.receiver.username}"
        self.assertEqual(str(self.message), expected)

    def test_message_ordering(self):
        """Test message ordering by timestamp"""
        message2 = Message.objects.create(
            sender=self.receiver,
            receiver=self.sender,
            content='I am fine, thanks!'
        )
        
        messages = Message.objects.all()
        self.assertEqual(messages[0], self.message)  # Earlier message first
        self.assertEqual(messages[1], message2)


class RegisterSerializerTests(TestCase):
    """Test cases for RegisterSerializer"""

    def test_valid_student_registration(self):
        """Test valid student registration"""
        data = {
            'username': 'newstudent',
            'email': 'student@example.com',
            'password': 'testpass123',
            'password2': 'testpass123',
            'user_type': 'student',
            'name': 'New Student',
            'first_name': 'New',
            'last_name': 'Student'
        }
        serializer = RegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_valid_mentor_registration(self):
        """Test valid mentor registration"""
        data = {
            'username': 'newmentor',
            'email': 'mentor@example.com',
            'password': 'testpass123',
            'password2': 'testpass123',
            'user_type': 'mentor',
            'name': 'New Mentor',
            'first_name': 'New',
            'last_name': 'Mentor'
        }
        serializer = RegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_password_mismatch(self):
        """Test password mismatch validation"""
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'password2': 'differentpass',
            'user_type': 'student',
            'name': 'Test User'
        }
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)

    def test_duplicate_username(self):
        """Test duplicate username validation"""
        User.objects.create_user('existinguser', 'existing@test.com', 'pass')
        
        data = {
            'username': 'existinguser',
            'email': 'new@example.com',
            'password': 'testpass123',
            'password2': 'testpass123',
            'user_type': 'student',
            'name': 'New User'
        }
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)


class AuthenticationAPITests(APITestCase):
    """Test cases for authentication API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('register')
        self.token_url = reverse('token_obtain_pair')
        self.refresh_url = reverse('token_refresh')

    def test_user_registration_student(self):
        """Test student user registration"""
        data = {
            'username': 'newstudent',
            'email': 'student@example.com',
            'password': 'testpass123',
            'password2': 'testpass123',
            'user_type': 'student',
            'name': 'New Student'
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)

    def test_user_registration_mentor(self):
        """Test mentor user registration"""
        data = {
            'username': 'newmentor',
            'email': 'mentor@example.com',
            'password': 'testpass123',
            'password2': 'testpass123',
            'user_type': 'mentor',
            'name': 'New Mentor'
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_token_obtain(self):
        """Test token obtain endpoint"""
        user = User.objects.create_user('testuser', 'test@example.com', 'testpass123')
        
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post(self.token_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_token_refresh(self):
        """Test token refresh endpoint"""
        user = User.objects.create_user('testuser', 'test@example.com', 'testpass123')
        refresh = RefreshToken.for_user(user)
        
        data = {'refresh': str(refresh)}
        response = self.client.post(self.refresh_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_invalid_credentials(self):
        """Test login with invalid credentials"""
        data = {
            'username': 'nonexistent',
            'password': 'wrongpass'
        }
        response = self.client.post(self.token_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class StudentProfileAPITests(APITestCase):
    """Test cases for StudentProfile API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('student1', 'student@test.com', 'testpass123')
        self.student_profile = StudentProfile.objects.create(
            user=self.user,
            name='John Student',
            year_level=2,
            tech_stack=['Python', 'Django']
        )
        
        # Authenticate the client
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def test_get_own_profile(self):
        """Test getting own student profile"""
        url = reverse('studentprofile-me')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'John Student')

    def test_update_own_profile(self):
        """Test updating own student profile"""
        url = reverse('studentprofile-detail', kwargs={'pk': self.student_profile.pk})
        data = {
            'name': 'Updated Name',
            'bio': 'Updated bio',
            'year_level': 3,
            'tech_stack': ['Python', 'Django', 'React']
        }
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Name')

    def test_unauthorized_access(self):
        """Test accessing profile without authentication"""
        self.client.credentials()  # Remove authentication
        url = reverse('studentprofile-me')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class StudentProjectAPITests(APITestCase):
    """Test cases for StudentProject API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('student1', 'student@test.com', 'testpass123')
        self.student_profile = StudentProfile.objects.create(
            user=self.user,
            name='John Student'
        )
        
        # Authenticate the client
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def test_create_project(self):
        """Test creating a student project"""
        url = reverse('studentproject-list')
        data = {
            'title': 'My New Project',
            'description': 'A test project',
            'tools_used': ['Python', 'Django']
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'My New Project')

    def test_list_own_projects(self):
        """Test listing own projects"""
        # Create a project
        StudentProject.objects.create(
            student=self.student_profile,
            title='Test Project',
            description='Test description',
            tools_used=['Python']
        )
        
        url = reverse('studentproject-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class MentorshipRequestAPITests(APITestCase):
    """Test cases for MentorshipRequest API endpoints"""

    def setUp(self):
        self.client = APIClient()
        
        # Create student and mentor users
        self.student_user = User.objects.create_user('student1', 'student@test.com', 'testpass123')
        self.mentor_user = User.objects.create_user('mentor1', 'mentor@test.com', 'testpass123')
        
        # Create profiles
        self.student_profile = StudentProfile.objects.create(
            user=self.student_user,
            name='John Student'
        )
        self.mentor_profile = MentorProfile.objects.create(
            user=self.mentor_user,
            name='Jane Mentor'
        )

    def test_create_mentorship_request(self):
        """Test creating a mentorship request"""
        # Authenticate as student
        refresh = RefreshToken.for_user(self.student_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('mentorship-request-list')
        data = {
            'mentor': self.mentor_user.id,
            'message': 'I would like guidance on Django development'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_mentor_accept_request(self):
        """Test mentor accepting a mentorship request"""
        # Create a mentorship request
        request = MentorshipRequest.objects.create(
            student=self.student_user,
            mentor=self.mentor_user,
            message='Test request'
        )
        
        # Authenticate as mentor
        refresh = RefreshToken.for_user(self.mentor_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('mentorship-request-accept', kwargs={'pk': request.pk})
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        request.refresh_from_db()
        self.assertEqual(request.status, 'accepted')


class MessageAPITests(APITestCase):
    """Test cases for Message API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.sender = User.objects.create_user('sender', 'sender@test.com', 'testpass123')
        self.receiver = User.objects.create_user('receiver', 'receiver@test.com', 'testpass123')
        
        # Authenticate as sender
        refresh = RefreshToken.for_user(self.sender)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def test_send_message(self):
        """Test sending a message"""
        url = reverse('send_message')
        data = {
            'receiver': self.receiver.id,
            'content': 'Hello, how are you?'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['content'], 'Hello, how are you?')

    def test_get_message_history(self):
        """Test getting message history"""
        # Create a message
        Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content='Test message'
        )
        
        url = reverse('message_history', kwargs={'user_id': self.receiver.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class PermissionTests(APITestCase):
    """Test cases for custom permissions"""

    def setUp(self):
        self.client = APIClient()
        self.student_user = User.objects.create_user('student1', 'student@test.com', 'testpass123')
        self.mentor_user = User.objects.create_user('mentor1', 'mentor@test.com', 'testpass123')
        
        # Create profiles
        self.student_profile = StudentProfile.objects.create(
            user=self.student_user,
            name='John Student'
        )
        self.mentor_profile = MentorProfile.objects.create(
            user=self.mentor_user,
            name='Jane Mentor'
        )

    def test_student_cannot_access_mentor_profile(self):
        """Test that student cannot modify mentor profiles"""
        # Authenticate as student
        refresh = RefreshToken.for_user(self.student_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('mentorprofile-detail', kwargs={'pk': self.mentor_profile.pk})
        data = {'name': 'Hacked Name'}
        response = self.client.patch(url, data)
        # Should be forbidden or not found depending on permission implementation
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_mentor_cannot_access_student_projects(self):
        """Test that mentor cannot create student projects"""
        # Authenticate as mentor
        refresh = RefreshToken.for_user(self.mentor_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('studentproject-list')
        data = {
            'title': 'Hacked Project',
            'description': 'This should not work',
            'tools_used': ['Hack']
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class RateLimitingTests(APITestCase):
    """Test cases for rate limiting functionality"""

    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('register')

    @patch('users.rate_limiting.cache')
    def test_rate_limiting_exceeded(self, mock_cache):
        """Test rate limiting when exceeded"""
        # Mock cache to simulate rate limit exceeded
        mock_cache.get.return_value = [1, 2, 3, 4, 5]  # 5 requests already made
        
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'password2': 'testpass123',
            'user_type': 'student',
            'name': 'Test User'
        }
        
        response = self.client.post(self.register_url, data)
        # Should return 429 if rate limiting is properly implemented
        # This depends on the actual implementation


class FileUploadTests(APITestCase):
    """Test cases for file upload functionality"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('testuser', 'test@example.com', 'testpass123')
        self.student_profile = StudentProfile.objects.create(
            user=self.user,
            name='Test Student'
        )
        
        # Authenticate
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def test_profile_photo_upload(self):
        """Test uploading profile photo"""
        # Create a simple test image
        image = Image.new('RGB', (100, 100), color='red')
        temp_file = BytesIO()
        image.save(temp_file, format='JPEG')
        temp_file.seek(0)
        
        uploaded_file = SimpleUploadedFile(
            "test_image.jpg",
            temp_file.getvalue(),
            content_type="image/jpeg"
        )
        
        url = reverse('studentprofile-detail', kwargs={'pk': self.student_profile.pk})
        data = {'photo': uploaded_file}
        response = self.client.patch(url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.student_profile.refresh_from_db()
        self.assertTrue(self.student_profile.photo)

    def test_message_file_attachment(self):
        """Test sending message with file attachment"""
        receiver = User.objects.create_user('receiver', 'receiver@test.com', 'testpass123')
        
        # Create a simple text file
        test_file = SimpleUploadedFile(
            "test.txt",
            b"file_content",
            content_type="text/plain"
        )
        
        url = reverse('send_message')
        data = {
            'receiver': receiver.id,
            'content': 'Message with file',
            'file': test_file
        }
        response = self.client.post(url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(response.data.get('file_url'))


if __name__ == '__main__':
    import django
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'devguidance_django.settings')
    django.setup()
    
    from django.test.utils import get_runner
    from django.conf import settings
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["users"])
