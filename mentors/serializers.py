from rest_framework import serializers
from django.contrib.auth.models import User
from .models import MentorProfile, MentorshipRequest
from students.models import StudentProfile

class MentorProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = MentorProfile
        fields = ['id', 'username', 'email', 'name', 'bio', 'expertise_tags', 
                 'years_of_experience', 'company', 'position', 'linkedin_profile', 
                 'github_profile', 'profile_picture', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class MentorListSerializer(serializers.ModelSerializer):
    mentor_profile = MentorProfileSerializer(source='mentors_profile', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'mentor_profile']

class MentorshipRequestSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.students_profile.name', read_only=True)
    mentor_name = serializers.CharField(source='mentor.mentors_profile.name', read_only=True)
    
    class Meta:
        model = MentorshipRequest
        fields = ['id', 'student', 'mentor', 'student_name', 'mentor_name', 'goal', 
                 'message', 'status', 'rejection_reason', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'status', 'rejection_reason']
