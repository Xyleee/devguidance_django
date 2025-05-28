from rest_framework import serializers
from django.contrib.auth.models import User
from .models import StudentProfile, StudentProject

class StudentProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = StudentProfile
        fields = ['id', 'username', 'email', 'name', 'bio', 'year_level', 
                 'tech_stack', 'profile_picture', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class StudentProjectSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.name', read_only=True)
    
    class Meta:
        model = StudentProject
        fields = ['id', 'student', 'student_name', 'title', 'description', 
                 'repo_link', 'demo_link', 'tools_used', 'created_at', 'updated_at']
        read_only_fields = ['id', 'student', 'created_at', 'updated_at']
