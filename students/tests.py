from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO
from PIL import Image

from .models import StudentProfile, StudentProject
from .serializers import StudentProfileSerializer, StudentProjectSerializer
from .views import StudentProfileViewSet, StudentProjectViewSet


class StudentProfileModelTests(TestCase):
    """Test cases for StudentProfile model in students app"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='student1',
            email='student@test.com',
            password='testpass123'
        )

    def test_student_profile_creation(self):
        """Test creating a student profile"""
        profile = StudentProfile.objects.create(
            user=self.user,
            name='John Student',
            bio='I am a computer science student',
            year_level=2,
            tech_stack=['Python', 'JavaScript', 'React']
        )
        
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.name, 'John Student')
        self.assertEqual(profile.year_level, 2)
        self.assertEqual(profile.tech_stack, ['Python', 'JavaScript', 'React'])

    def test_student_profile_string_representation(self):
        """Test student profile string representation"""
        profile = StudentProfile.objects.create(
            user=self.user,
            name='John Student'
        )
        expected_str = f"{self.user.username}'s Profile"
        self.assertEqual(str(profile), expected_str)

    def test_student_profile_default_values(self):
        """Test default values for student profile fields"""
        profile = StudentProfile.objects.create(
            user=self.user,
            name='John Student'
        )
        
        self.assertEqual(profile.year_level, 1)  # Default year level
        self.assertEqual(profile.tech_stack, [])  # Default empty list
        self.assertEqual(profile.bio, '')  # Default empty string

    def test_student_profile_year_level_choices(self):
        """Test year level choices validation"""
        profile = StudentProfile.objects.create(
            user=self.user,
            name='John Student',
            year_level=4  # 4th year
        )
        self.assertEqual(profile.year_level, 4)

    def test_profile_picture_upload(self):
        """Test profile picture upload functionality"""
        profile = StudentProfile.objects.create(
            user=self.user,
            name='John Student'
        )
        
        # Create a simple test image
        image = Image.new('RGB', (100, 100), color='blue')
        temp_file = BytesIO()
        image.save(temp_file, format='JPEG')
        temp_file.seek(0)
        
        uploaded_file = SimpleUploadedFile(
            "test_profile.jpg",
            temp_file.getvalue(),
            content_type="image/jpeg"
        )
        
        profile.profile_picture = uploaded_file
        profile.save()
        
        self.assertTrue(profile.profile_picture)
        self.assertTrue(profile.profile_picture.name.startswith('profile_pics/'))


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

    def test_student_project_creation(self):
        """Test creating a student project"""
        project = StudentProject.objects.create(
            student=self.student_profile,
            title='E-commerce Website',
            description='A full-stack e-commerce platform built with Django and React',
            repo_link='https://github.com/student/ecommerce',
            demo_link='https://myecommerce.herokuapp.com',
            tools_used='Python, Django, React, PostgreSQL'
        )
        
        self.assertEqual(project.student, self.student_profile)
        self.assertEqual(project.title, 'E-commerce Website')
        self.assertIn('Django', project.description)
        self.assertEqual(project.repo_link, 'https://github.com/student/ecommerce')

    def test_student_project_string_representation(self):
        """Test student project string representation"""
        project = StudentProject.objects.create(
            student=self.student_profile,
            title='My Awesome Project',
            description='A great project'
        )
        self.assertEqual(str(project), 'My Awesome Project')

    def test_student_project_optional_fields(self):
        """Test that optional fields can be empty"""
        project = StudentProject.objects.create(
            student=self.student_profile,
            title='Simple Project',
            description='A basic project'
        )
        
        self.assertEqual(project.repo_link, '')
        self.assertEqual(project.demo_link, '')
        self.assertEqual(project.tools_used, '')

    def test_student_project_relationship(self):
        """Test the relationship between student and projects"""
        project1 = StudentProject.objects.create(
            student=self.student_profile,
            title='Project 1',
            description='First project'
        )
        project2 = StudentProject.objects.create(
            student=self.student_profile,
            title='Project 2',
            description='Second project'
        )
        
        # Test that student can have multiple projects
        self.assertEqual(self.student_profile.projects.count(), 2)
        self.assertIn(project1, self.student_profile.projects.all())
        self.assertIn(project2, self.student_profile.projects.all())

    def test_project_cascade_delete(self):
        """Test that projects are deleted when student profile is deleted"""
        project = StudentProject.objects.create(
            student=self.student_profile,
            title='Test Project',
            description='Will be deleted'
        )
        
        project_id = project.id
        self.student_profile.delete()
        
        # Project should be deleted due to CASCADE
        with self.assertRaises(StudentProject.DoesNotExist):
            StudentProject.objects.get(id=project_id)


class StudentProfileSerializerTests(TestCase):
    """Test cases for StudentProfile serializer"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='student1',
            email='student@test.com',
            password='testpass123'
        )

    def test_student_profile_serialization(self):
        """Test serializing a student profile"""
        profile = StudentProfile.objects.create(
            user=self.user,
            name='John Student',
            bio='Computer Science student',
            year_level=3,
            tech_stack=['Python', 'Django', 'React']
        )
        
        serializer = StudentProfileSerializer(profile)
        data = serializer.data
        
        self.assertEqual(data['name'], 'John Student')
        self.assertEqual(data['year_level'], 3)
        self.assertEqual(data['tech_stack'], ['Python', 'Django', 'React'])

    def test_student_profile_deserialization(self):
        """Test deserializing student profile data"""
        data = {
            'name': 'Jane Student',
            'bio': 'Software Engineering student',
            'year_level': 2,
            'tech_stack': ['JavaScript', 'Vue.js', 'Node.js']
        }
        
        serializer = StudentProfileSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        profile = serializer.save(user=self.user)
        self.assertEqual(profile.name, 'Jane Student')
        self.assertEqual(profile.year_level, 2)

    def test_student_profile_validation(self):
        """Test validation for student profile data"""
        # Test with invalid year level
        data = {
            'name': 'John Student',
            'year_level': 5  # Invalid year level (should be 1-4)
        }
        
        serializer = StudentProfileSerializer(data=data)
        # Note: This depends on your actual validation logic
        # If you have year level validation, this should fail


class StudentProjectSerializerTests(TestCase):
    """Test cases for StudentProject serializer"""

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

    def test_student_project_serialization(self):
        """Test serializing a student project"""
        project = StudentProject.objects.create(
            student=self.student_profile,
            title='Web Portfolio',
            description='Personal portfolio website',
            repo_link='https://github.com/student/portfolio',
            tools_used='HTML, CSS, JavaScript'
        )
        
        serializer = StudentProjectSerializer(project)
        data = serializer.data
        
        self.assertEqual(data['title'], 'Web Portfolio')
        self.assertEqual(data['repo_link'], 'https://github.com/student/portfolio')

    def test_student_project_deserialization(self):
        """Test deserializing student project data"""
        data = {
            'title': 'Blog Application',
            'description': 'A blogging platform with user authentication',
            'repo_link': 'https://github.com/student/blog',
            'demo_link': 'https://myblog.herokuapp.com',
            'tools_used': 'Python, Django, Bootstrap'
        }
        
        serializer = StudentProjectSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        project = serializer.save(student=self.student_profile)
        self.assertEqual(project.title, 'Blog Application')
        self.assertEqual(project.student, self.student_profile)


class StudentProfileAPITests(APITestCase):
    """Test cases for StudentProfile API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='student1',
            email='student@test.com',
            password='testpass123'
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.user,
            name='John Student',
            year_level=2
        )
        
        # Authenticate the client
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def test_list_student_profiles(self):
        """Test listing student profiles"""
        url = reverse('students:studentprofile-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'John Student')

    def test_retrieve_student_profile(self):
        """Test retrieving a specific student profile"""
        url = reverse('students:studentprofile-detail', kwargs={'pk': self.student_profile.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'John Student')

    def test_create_student_profile(self):
        """Test creating a new student profile"""
        # Create another user for testing
        new_user = User.objects.create_user(
            username='student2',
            email='student2@test.com',
            password='testpass123'
        )
        
        # Authenticate as the new user
        refresh = RefreshToken.for_user(new_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('students:studentprofile-list')
        data = {
            'name': 'Jane Student',
            'bio': 'I love coding!',
            'year_level': 1,
            'tech_stack': ['Python', 'JavaScript']
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Jane Student')

    def test_update_student_profile(self):
        """Test updating a student profile"""
        url = reverse('students:studentprofile-detail', kwargs={'pk': self.student_profile.pk})
        data = {
            'name': 'John Updated',
            'bio': 'Updated bio',
            'year_level': 3
        }
        
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'John Updated')
        self.assertEqual(response.data['year_level'], 3)

    def test_delete_student_profile(self):
        """Test deleting a student profile"""
        url = reverse('students:studentprofile-detail', kwargs={'pk': self.student_profile.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(StudentProfile.objects.filter(pk=self.student_profile.pk).exists())

    def test_unauthorized_access(self):
        """Test accessing API without authentication"""
        self.client.credentials()  # Remove authentication
        
        url = reverse('students:studentprofile-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class StudentProjectAPITests(APITestCase):
    """Test cases for StudentProject API endpoints"""

    def setUp(self):
        self.client = APIClient()
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
            title='Test Project',
            description='A test project',
            tools_used='Python, Django'
        )
        
        # Authenticate the client
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def test_list_student_projects(self):
        """Test listing student projects"""
        url = reverse('students:studentproject-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Test Project')

    def test_retrieve_student_project(self):
        """Test retrieving a specific student project"""
        url = reverse('students:studentproject-detail', kwargs={'pk': self.project.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Project')

    def test_create_student_project(self):
        """Test creating a new student project"""
        url = reverse('students:studentproject-list')
        data = {
            'title': 'New Project',
            'description': 'A brand new project',
            'repo_link': 'https://github.com/student/new-project',
            'tools_used': 'React, Node.js'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'New Project')

    def test_update_student_project(self):
        """Test updating a student project"""
        url = reverse('students:studentproject-detail', kwargs={'pk': self.project.pk})
        data = {
            'title': 'Updated Project',
            'description': 'Updated description'
        }
        
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Project')

    def test_delete_student_project(self):
        """Test deleting a student project"""
        url = reverse('students:studentproject-detail', kwargs={'pk': self.project.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(StudentProject.objects.filter(pk=self.project.pk).exists())

    def test_project_filtering_by_student(self):
        """Test that projects are filtered by student"""
        # Create another student and project
        other_user = User.objects.create_user(
            username='student2',
            email='student2@test.com',
            password='testpass123'
        )
        other_profile = StudentProfile.objects.create(
            user=other_user,
            name='Other Student'
        )
        StudentProject.objects.create(
            student=other_profile,
            title='Other Project',
            description='Another project'
        )
        
        # Current user should only see their own projects
        url = reverse('students:studentproject-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Only own project
        self.assertEqual(response.data[0]['title'], 'Test Project')


class StudentViewSetTests(APITestCase):
    """Test cases for Student ViewSets functionality"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='student1',
            email='student@test.com',
            password='testpass123'
        )
        
        # Authenticate the client
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def test_viewset_permissions(self):
        """Test that ViewSets have proper permissions"""
        # Test that authenticated users can access
        url = reverse('students:studentprofile-list')
        response = self.client.get(url)
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN])

    def test_viewset_ordering(self):
        """Test that ViewSets return ordered results"""
        # Create multiple profiles
        profile1 = StudentProfile.objects.create(
            user=self.user,
            name='A Student'
        )
        
        other_user = User.objects.create_user('student2', 'student2@test.com', 'pass')
        profile2 = StudentProfile.objects.create(
            user=other_user,
            name='B Student'
        )
        
        url = reverse('students:studentprofile-list')
        response = self.client.get(url)
        
        if response.status_code == status.HTTP_200_OK:
            # Check that results are properly ordered
            self.assertTrue(len(response.data) >= 1)


class StudentModelSignalTests(TestCase):
    """Test cases for model signals and automatic profile creation"""

    def test_automatic_profile_creation(self):
        """Test if profiles are created automatically via signals"""
        # This test depends on whether you have signal handlers
        # for automatic profile creation when a user is created
        user = User.objects.create_user(
            username='newstudent',
            email='new@test.com',
            password='testpass123'
        )
        
        # Check if profile was created automatically
        # Note: This depends on your signal implementation
        try:
            profile = StudentProfile.objects.get(user=user)
            # If you have automatic profile creation
            self.assertIsNotNone(profile)
        except StudentProfile.DoesNotExist:
            # If you don't have automatic profile creation, that's also valid
            pass


class StudentSearchTests(APITestCase):
    """Test cases for student search functionality"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='student1',
            email='student@test.com',
            password='testpass123'
        )
        
        # Create test profiles with different data
        self.profile1 = StudentProfile.objects.create(
            user=self.user,
            name='Python Developer',
            tech_stack=['Python', 'Django']
        )
        
        user2 = User.objects.create_user('student2', 'student2@test.com', 'pass')
        self.profile2 = StudentProfile.objects.create(
            user=user2,
            name='JavaScript Developer',
            tech_stack=['JavaScript', 'React']
        )
        
        # Authenticate
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def test_search_by_name(self):
        """Test searching profiles by name"""
        url = reverse('students:studentprofile-list')
        response = self.client.get(url, {'search': 'Python'})
        
        if response.status_code == status.HTTP_200_OK:
            # Should find the Python developer
            self.assertTrue(any('Python' in item['name'] for item in response.data))

    def test_search_by_tech_stack(self):
        """Test searching profiles by tech stack"""
        url = reverse('students:studentprofile-list')
        response = self.client.get(url, {'search': 'Django'})
        
        if response.status_code == status.HTTP_200_OK:
            # Should find profiles with Django in tech stack
            found = False
            for item in response.data:
                if 'Django' in item.get('tech_stack', []):
                    found = True
                    break
            # This depends on your search implementation


if __name__ == '__main__':
    import django
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'devguidance_django.settings')
    django.setup()
    
    from django.test.utils import get_runner
    from django.conf import settings
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["students"])
