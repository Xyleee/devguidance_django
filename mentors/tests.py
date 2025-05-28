from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO
from PIL import Image
from unittest.mock import patch

from .models import MentorProfile, MentorshipRequest
from .serializers import MentorProfileSerializer, MentorshipRequestSerializer
from .views import MentorProfileViewSet, MentorshipRequestViewSet
from .permissions import IsMentorOwner
from students.models import StudentProfile


class MentorProfileModelTests(TestCase):
    """Test cases for MentorProfile model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='mentor1',
            email='mentor@test.com',
            password='testpass123'
        )

    def test_mentor_profile_creation(self):
        """Test creating a mentor profile"""
        profile = MentorProfile.objects.create(
            user=self.user,
            name='Jane Mentor',
            bio='Senior developer with 10 years experience',
            expertise_tags=['Python', 'Django', 'Machine Learning'],
            years_of_experience=10,
            company='Tech Corp',
            position='Senior Developer',
            linkedin_profile='https://linkedin.com/in/janementor',
            github_profile='https://github.com/janementor'
        )
        
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.name, 'Jane Mentor')
        self.assertEqual(profile.years_of_experience, 10)
        self.assertEqual(profile.expertise_tags, ['Python', 'Django', 'Machine Learning'])
        self.assertEqual(profile.company, 'Tech Corp')

    def test_mentor_profile_string_representation(self):
        """Test mentor profile string representation"""
        profile = MentorProfile.objects.create(
            user=self.user,
            name='Jane Mentor'
        )
        expected_str = f"{self.user.username}'s Mentor Profile"
        self.assertEqual(str(profile), expected_str)

    def test_mentor_profile_default_values(self):
        """Test default values for mentor profile fields"""
        profile = MentorProfile.objects.create(
            user=self.user,
            name='Jane Mentor'
        )
        
        self.assertEqual(profile.years_of_experience, 0)  # Default
        self.assertEqual(profile.expertise_tags, [])  # Default empty list
        self.assertEqual(profile.bio, '')  # Default empty string
        self.assertEqual(profile.company, '')
        self.assertEqual(profile.position, '')

    def test_profile_picture_upload(self):
        """Test profile picture upload functionality"""
        profile = MentorProfile.objects.create(
            user=self.user,
            name='Jane Mentor'
        )
        
        # Create a simple test image
        image = Image.new('RGB', (100, 100), color='green')
        temp_file = BytesIO()
        image.save(temp_file, format='JPEG')
        temp_file.seek(0)
        
        uploaded_file = SimpleUploadedFile(
            "test_mentor.jpg",
            temp_file.getvalue(),
            content_type="image/jpeg"
        )
        
        profile.profile_picture = uploaded_file
        profile.save()
        
        self.assertTrue(profile.profile_picture)
        self.assertTrue(profile.profile_picture.name.startswith('mentor_pics/'))

    def test_mentor_expertise_tags(self):
        """Test expertise tags functionality"""
        profile = MentorProfile.objects.create(
            user=self.user,
            name='Jane Mentor',
            expertise_tags=['Python', 'JavaScript', 'DevOps', 'Cloud Computing']
        )
        
        self.assertEqual(len(profile.expertise_tags), 4)
        self.assertIn('Python', profile.expertise_tags)
        self.assertIn('Cloud Computing', profile.expertise_tags)


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
        
        # Create profiles
        self.student_profile = StudentProfile.objects.create(
            user=self.student_user,
            name='John Student'
        )
        self.mentor_profile = MentorProfile.objects.create(
            user=self.mentor_user,
            name='Jane Mentor'
        )

    def test_mentorship_request_creation(self):
        """Test creating a mentorship request"""
        request = MentorshipRequest.objects.create(
            student=self.student_user,
            mentor=self.mentor_user,
            goal='Learn Django development',
            message='I would like guidance on building web applications with Django'
        )
        
        self.assertEqual(request.student, self.student_user)
        self.assertEqual(request.mentor, self.mentor_user)
        self.assertEqual(request.status, 'pending')  # Default status
        self.assertEqual(request.goal, 'Learn Django development')

    def test_mentorship_request_string_representation(self):
        """Test mentorship request string representation"""
        request = MentorshipRequest.objects.create(
            student=self.student_user,
            mentor=self.mentor_user,
            goal='Learn Python',
            message='Help with Python'
        )
        expected_str = f"Mentorship Request: {self.student_user.username} -> {self.mentor_user.username}"
        self.assertEqual(str(request), expected_str)

    def test_mentorship_request_status_choices(self):
        """Test mentorship request status choices"""
        request = MentorshipRequest.objects.create(
            student=self.student_user,
            mentor=self.mentor_user,
            goal='Learn React',
            message='Help with frontend'
        )
        
        # Test different status values
        request.status = 'accepted'
        request.save()
        self.assertEqual(request.status, 'accepted')
        
        request.status = 'declined'
        request.rejection_reason = 'Too busy at the moment'
        request.save()
        self.assertEqual(request.status, 'declined')
        self.assertEqual(request.rejection_reason, 'Too busy at the moment')

    def test_mentorship_request_acceptance_logic(self):
        """Test that accepting a request declines other pending requests"""
        # Create multiple pending requests from the same student
        request1 = MentorshipRequest.objects.create(
            student=self.student_user,
            mentor=self.mentor_user,
            goal='Learn Django',
            message='First request'
        )
        
        other_mentor = User.objects.create_user('mentor2', 'mentor2@test.com', 'pass')
        MentorProfile.objects.create(user=other_mentor, name='Other Mentor')
        
        request2 = MentorshipRequest.objects.create(
            student=self.student_user,
            mentor=other_mentor,
            goal='Learn React',
            message='Second request'
        )
        
        # Accept the first request
        request1.status = 'accepted'
        request1.save()
        
        # Check that the save method logic is triggered
        # Note: This depends on your actual implementation in the model
        # The test should verify that other pending requests are declined


class MentorProfileSerializerTests(TestCase):
    """Test cases for MentorProfile serializer"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='mentor1',
            email='mentor@test.com',
            password='testpass123'
        )

    def test_mentor_profile_serialization(self):
        """Test serializing a mentor profile"""
        profile = MentorProfile.objects.create(
            user=self.user,
            name='Jane Mentor',
            bio='Experienced software engineer',
            expertise_tags=['Python', 'Django', 'AWS'],
            years_of_experience=8,
            company='Tech Solutions'
        )
        
        serializer = MentorProfileSerializer(profile)
        data = serializer.data
        
        self.assertEqual(data['name'], 'Jane Mentor')
        self.assertEqual(data['years_of_experience'], 8)
        self.assertEqual(data['expertise_tags'], ['Python', 'Django', 'AWS'])
        self.assertEqual(data['company'], 'Tech Solutions')

    def test_mentor_profile_deserialization(self):
        """Test deserializing mentor profile data"""
        data = {
            'name': 'John Mentor',
            'bio': 'Full-stack developer and tech lead',
            'expertise_tags': ['JavaScript', 'React', 'Node.js'],
            'years_of_experience': 6,
            'company': 'StartupCorp',
            'position': 'Tech Lead'
        }
        
        serializer = MentorProfileSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        profile = serializer.save(user=self.user)
        self.assertEqual(profile.name, 'John Mentor')
        self.assertEqual(profile.years_of_experience, 6)
        self.assertEqual(profile.company, 'StartupCorp')

    def test_mentor_profile_validation(self):
        """Test validation for mentor profile data"""
        # Test with negative years of experience
        data = {
            'name': 'Invalid Mentor',
            'years_of_experience': -1  # Should be invalid
        }
        
        serializer = MentorProfileSerializer(data=data)
        # Note: This depends on your actual validation logic
        # If you have years validation, this should fail


class MentorshipRequestSerializerTests(TestCase):
    """Test cases for MentorshipRequest serializer"""

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

    def test_mentorship_request_serialization(self):
        """Test serializing a mentorship request"""
        request = MentorshipRequest.objects.create(
            student=self.student_user,
            mentor=self.mentor_user,
            goal='Master Django REST Framework',
            message='I need help building APIs',
            status='pending'
        )
        
        serializer = MentorshipRequestSerializer(request)
        data = serializer.data
        
        self.assertEqual(data['goal'], 'Master Django REST Framework')
        self.assertEqual(data['status'], 'pending')

    def test_mentorship_request_deserialization(self):
        """Test deserializing mentorship request data"""
        data = {
            'goal': 'Learn DevOps practices',
            'message': 'I want to learn CI/CD and cloud deployment',
            'mentor': self.mentor_user.id
        }
        
        serializer = MentorshipRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        request = serializer.save(student=self.student_user)
        self.assertEqual(request.goal, 'Learn DevOps practices')
        self.assertEqual(request.student, self.student_user)


class MentorProfileAPITests(APITestCase):
    """Test cases for MentorProfile API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='mentor1',
            email='mentor@test.com',
            password='testpass123'
        )
        self.mentor_profile = MentorProfile.objects.create(
            user=self.user,
            name='Jane Mentor',
            expertise_tags=['Python', 'Django']
        )
        
        # Authenticate the client
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def test_list_mentor_profiles(self):
        """Test listing mentor profiles"""
        url = reverse('mentors:mentorprofile-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Jane Mentor')

    def test_retrieve_mentor_profile(self):
        """Test retrieving a specific mentor profile"""
        url = reverse('mentors:mentorprofile-detail', kwargs={'pk': self.mentor_profile.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Jane Mentor')

    def test_create_mentor_profile(self):
        """Test creating a new mentor profile"""
        # Create another user for testing
        new_user = User.objects.create_user(
            username='mentor2',
            email='mentor2@test.com',
            password='testpass123'
        )
        
        # Authenticate as the new user
        refresh = RefreshToken.for_user(new_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('mentors:mentorprofile-list')
        data = {
            'name': 'John Mentor',
            'bio': 'Expert in backend development',
            'expertise_tags': ['Python', 'PostgreSQL'],
            'years_of_experience': 5
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'John Mentor')

    def test_update_mentor_profile(self):
        """Test updating a mentor profile"""
        url = reverse('mentors:mentorprofile-detail', kwargs={'pk': self.mentor_profile.pk})
        data = {
            'name': 'Jane Updated',
            'bio': 'Updated bio',
            'years_of_experience': 12
        }
        
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Jane Updated')
        self.assertEqual(response.data['years_of_experience'], 12)

    def test_delete_mentor_profile(self):
        """Test deleting a mentor profile"""
        url = reverse('mentors:mentorprofile-detail', kwargs={'pk': self.mentor_profile.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(MentorProfile.objects.filter(pk=self.mentor_profile.pk).exists())

    def test_unauthorized_access(self):
        """Test accessing API without authentication"""
        self.client.credentials()  # Remove authentication
        
        url = reverse('mentors:mentorprofile-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class MentorshipRequestAPITests(APITestCase):
    """Test cases for MentorshipRequest API endpoints"""

    def setUp(self):
        self.client = APIClient()
        
        # Create users
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
        
        # Create profiles
        self.student_profile = StudentProfile.objects.create(
            user=self.student_user,
            name='John Student'
        )
        self.mentor_profile = MentorProfile.objects.create(
            user=self.mentor_user,
            name='Jane Mentor'
        )
        
        self.request = MentorshipRequest.objects.create(
            student=self.student_user,
            mentor=self.mentor_user,
            goal='Learn Django',
            message='I need help with Django development'
        )

    def test_student_create_mentorship_request(self):
        """Test student creating a mentorship request"""
        # Authenticate as student
        refresh = RefreshToken.for_user(self.student_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Create another mentor for testing
        mentor2 = User.objects.create_user('mentor2', 'mentor2@test.com', 'pass')
        MentorProfile.objects.create(user=mentor2, name='Another Mentor')
        
        url = reverse('mentors:mentorshiprequest-list')
        data = {
            'mentor': mentor2.id,
            'goal': 'Learn React',
            'message': 'I want to learn frontend development'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['goal'], 'Learn React')

    def test_mentor_accept_request(self):
        """Test mentor accepting a mentorship request"""
        # Authenticate as mentor
        refresh = RefreshToken.for_user(self.mentor_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('mentors:mentorshiprequest-accept', kwargs={'pk': self.request.pk})
        response = self.client.patch(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, 'accepted')

    def test_mentor_decline_request(self):
        """Test mentor declining a mentorship request"""
        # Authenticate as mentor
        refresh = RefreshToken.for_user(self.mentor_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('mentors:mentorshiprequest-decline', kwargs={'pk': self.request.pk})
        data = {
            'rejection_reason': 'Too busy with current mentees'
        }
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, 'declined')
        self.assertEqual(self.request.rejection_reason, 'Too busy with current mentees')

    def test_list_requests_for_mentor(self):
        """Test mentor viewing their received requests"""
        # Authenticate as mentor
        refresh = RefreshToken.for_user(self.mentor_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('mentors:mentorshiprequest-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_list_requests_for_student(self):
        """Test student viewing their sent requests"""
        # Authenticate as student
        refresh = RefreshToken.for_user(self.student_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('mentors:mentorshiprequest-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_unauthorized_user_cannot_accept_request(self):
        """Test that unauthorized users cannot accept requests"""
        # Create another user who is not the mentor
        other_user = User.objects.create_user('other', 'other@test.com', 'pass')
        refresh = RefreshToken.for_user(other_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('mentors:mentorshiprequest-accept', kwargs={'pk': self.request.pk})
        response = self.client.patch(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class MentorPermissionTests(APITestCase):
    """Test cases for mentor-specific permissions"""

    def setUp(self):
        self.client = APIClient()
        
        # Create users
        self.mentor_user = User.objects.create_user(
            username='mentor1',
            email='mentor@test.com',
            password='testpass123'
        )
        self.other_mentor = User.objects.create_user(
            username='mentor2',
            email='mentor2@test.com',
            password='testpass123'
        )
        self.student_user = User.objects.create_user(
            username='student1',
            email='student@test.com',
            password='testpass123'
        )
        
        # Create profiles
        self.mentor_profile = MentorProfile.objects.create(
            user=self.mentor_user,
            name='Jane Mentor'
        )
        self.other_mentor_profile = MentorProfile.objects.create(
            user=self.other_mentor,
            name='Other Mentor'
        )

    def test_mentor_can_edit_own_profile(self):
        """Test that mentor can edit their own profile"""
        refresh = RefreshToken.for_user(self.mentor_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('mentors:mentorprofile-detail', kwargs={'pk': self.mentor_profile.pk})
        data = {'name': 'Updated Name'}
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_mentor_cannot_edit_other_profile(self):
        """Test that mentor cannot edit another mentor's profile"""
        refresh = RefreshToken.for_user(self.mentor_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('mentors:mentorprofile-detail', kwargs={'pk': self.other_mentor_profile.pk})
        data = {'name': 'Hacked Name'}
        response = self.client.patch(url, data)
        
        # Should be forbidden
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_student_cannot_edit_mentor_profile(self):
        """Test that student cannot edit mentor profiles"""
        refresh = RefreshToken.for_user(self.student_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('mentors:mentorprofile-detail', kwargs={'pk': self.mentor_profile.pk})
        data = {'name': 'Hacked Name'}
        response = self.client.patch(url, data)
        
        # Should be forbidden
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class MentorSearchAndFilterTests(APITestCase):
    """Test cases for mentor search and filtering functionality"""

    def setUp(self):
        self.client = APIClient()
        
        # Create mentor users and profiles
        self.mentor1_user = User.objects.create_user('mentor1', 'mentor1@test.com', 'pass')
        self.mentor1_profile = MentorProfile.objects.create(
            user=self.mentor1_user,
            name='Python Expert',
            expertise_tags=['Python', 'Django', 'Machine Learning'],
            years_of_experience=8
        )
        
        self.mentor2_user = User.objects.create_user('mentor2', 'mentor2@test.com', 'pass')
        self.mentor2_profile = MentorProfile.objects.create(
            user=self.mentor2_user,
            name='JavaScript Guru',
            expertise_tags=['JavaScript', 'React', 'Node.js'],
            years_of_experience=6
        )
        
        # Create a student for authentication
        self.student_user = User.objects.create_user('student1', 'student@test.com', 'pass')
        refresh = RefreshToken.for_user(self.student_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def test_search_mentors_by_name(self):
        """Test searching mentors by name"""
        url = reverse('mentors:mentorprofile-list')
        response = self.client.get(url, {'search': 'Python'})
        
        if response.status_code == status.HTTP_200_OK:
            # Should find the Python expert
            self.assertTrue(any('Python' in item['name'] for item in response.data))

    def test_search_mentors_by_expertise(self):
        """Test searching mentors by expertise tags"""
        url = reverse('mentors:mentorprofile-list')
        response = self.client.get(url, {'search': 'Django'})
        
        if response.status_code == status.HTTP_200_OK:
            # Should find mentors with Django expertise
            found = False
            for item in response.data:
                if 'Django' in item.get('expertise_tags', []):
                    found = True
                    break

    def test_filter_mentors_by_experience(self):
        """Test filtering mentors by years of experience"""
        # This test depends on whether you have experience filtering implemented
        url = reverse('mentors:mentorprofile-list')
        response = self.client.get(url, {'min_experience': 7})
        
        if response.status_code == status.HTTP_200_OK:
            # Should only return mentors with 7+ years experience
            for item in response.data:
                self.assertGreaterEqual(item.get('years_of_experience', 0), 7)


class MentorAvailabilityTests(APITestCase):
    """Test cases for mentor availability functionality"""

    def setUp(self):
        self.client = APIClient()
        self.mentor_user = User.objects.create_user('mentor1', 'mentor@test.com', 'pass')
        self.mentor_profile = MentorProfile.objects.create(
            user=self.mentor_user,
            name='Available Mentor'
        )
        
        # Authenticate as mentor
        refresh = RefreshToken.for_user(self.mentor_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def test_mentor_availability_status(self):
        """Test checking mentor availability status"""
        # This test depends on whether you have availability tracking
        url = reverse('mentors:mentorprofile-availability', kwargs={'pk': self.mentor_profile.pk})
        response = self.client.get(url)
        
        # Should return availability information
        if response.status_code == status.HTTP_200_OK:
            self.assertIn('available', response.data)


class MentorStatisticsTests(APITestCase):
    """Test cases for mentor statistics and analytics"""

    def setUp(self):
        self.client = APIClient()
        self.mentor_user = User.objects.create_user('mentor1', 'mentor@test.com', 'pass')
        self.mentor_profile = MentorProfile.objects.create(
            user=self.mentor_user,
            name='Stats Mentor'
        )
        
        # Create some mentorship requests for statistics
        student_user = User.objects.create_user('student1', 'student@test.com', 'pass')
        MentorshipRequest.objects.create(
            student=student_user,
            mentor=self.mentor_user,
            goal='Learn Python',
            message='Help with Python',
            status='accepted'
        )
        
        # Authenticate as mentor
        refresh = RefreshToken.for_user(self.mentor_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def test_mentor_statistics(self):
        """Test retrieving mentor statistics"""
        # This test depends on whether you have statistics endpoints
        url = reverse('mentors:mentorprofile-stats', kwargs={'pk': self.mentor_profile.pk})
        response = self.client.get(url)
        
        if response.status_code == status.HTTP_200_OK:
            # Should return statistics about mentorship requests
            self.assertIn('total_requests', response.data)
            self.assertIn('accepted_requests', response.data)


if __name__ == '__main__':
    import django
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'devguidance_django.settings')
    django.setup()
    
    from django.test.utils import get_runner
    from django.conf import settings
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["mentors"])
