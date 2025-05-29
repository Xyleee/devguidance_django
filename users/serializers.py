from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .models import Message
from students.models import StudentProfile, StudentProject
from mentors.models import MentorProfile, MentorshipRequest
from django.core.files.uploadedfile import UploadedFile
from django.core.exceptions import ValidationError
import os
import magic

class PhotoValidationMixin:
    """Mixin for validating photo uploads"""
    
    def validate_profile_picture(self, profile_picture):
        if not profile_picture:
            return profile_picture
            
        # Validate file size (2MB max)
        if profile_picture.size > 2 * 1024 * 1024:  # 2MB in bytes
            raise serializers.ValidationError("Image file too large. Maximum size is 2MB.")
            
        # Validate file type
        mime = magic.Magic(mime=True)
        file_type = mime.from_buffer(profile_picture.read())
        profile_picture.seek(0)  # Reset file pointer after reading
        
        valid_types = ['image/jpeg', 'image/png', 'image/webp']
        if file_type not in valid_types:
            raise serializers.ValidationError(
                "Invalid image format. Only JPEG, PNG, and WebP are supported."
            )
            
        return profile_picture

class RegisterSerializer(serializers.ModelSerializer, PhotoValidationMixin):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    user_type = serializers.ChoiceField(choices=['student', 'mentor'], required=True)
    name = serializers.CharField(required=True)
    profile_picture = serializers.ImageField(required=False)
    
    class Meta:
        model = User
        fields = ('username', 'password', 'password2', 'email', 'first_name', 'last_name', 'user_type', 'name', 'profile_picture')
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False},
            'email': {'required': True}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        # Remove user_type and name from attrs to prevent them being used in User creation
        self.user_type = attrs.pop('user_type')
        self.name = attrs.pop('name')
        
        # Handle profile_picture separately
        self.profile_picture = None
        if 'profile_picture' in attrs:
            self.profile_picture = attrs.pop('profile_picture')
            if self.profile_picture:
                self.validate_profile_picture(self.profile_picture)
                
        return attrs

    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        # Password hashing is handled automatically by set_password
        user.set_password(validated_data['password'])
        user.save()
        
        # Create the appropriate profile based on user_type
        if self.user_type == 'student':
            profile = StudentProfile.objects.create(
                user=user,
                name=self.name
            )
        elif self.user_type == 'mentor':
            profile = MentorProfile.objects.create(
                user=user,
                name=self.name
            )
        
        # Add profile_picture if provided
        if self.profile_picture:
            profile.profile_picture = self.profile_picture
            profile.save()
            
        return user

class StudentProfileSerializer(serializers.ModelSerializer, PhotoValidationMixin):
    projects = serializers.SerializerMethodField()
    profile_picture_url = serializers.SerializerMethodField()
    
    class Meta:
        model = StudentProfile
        fields = ['id', 'name', 'bio', 'year_level', 'tech_stack', 'projects', 'profile_picture', 'profile_picture_url', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
        extra_kwargs = {
            'profile_picture': {'write_only': True}
        }
    
    def get_projects(self, obj):
        projects = obj.projects.all()
        return StudentProjectSerializer(projects, many=True).data
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        
        if 'profile_picture' in validated_data:
            profile_picture = validated_data['profile_picture']
            if profile_picture:
                self.validate_profile_picture(profile_picture)
                
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        if 'profile_picture' in validated_data:
            profile_picture = validated_data['profile_picture']
            if profile_picture:
                self.validate_profile_picture(profile_picture)
                
        return super().update(instance, validated_data)
    
    def get_profile_picture_url(self, obj):
        if obj.profile_picture:
            return obj.profile_picture.url
        return None

class StudentProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProject
        fields = ['id', 'title', 'description', 'repo_link', 'demo_link', 'tools_used', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class MentorProfileSerializer(serializers.ModelSerializer, PhotoValidationMixin):
    profile_picture_url = serializers.SerializerMethodField()
    
    class Meta:
        model = MentorProfile
        fields = ['id', 'name', 'bio', 'years_of_experience', 'expertise_tags', 'company', 'position', 'linkedin_profile', 'github_profile', 'profile_picture', 'profile_picture_url', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
        extra_kwargs = {
            'profile_picture': {'write_only': True}
        }
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        
        if 'profile_picture' in validated_data:
            profile_picture = validated_data['profile_picture']
            if profile_picture:
                self.validate_profile_picture(profile_picture)
                
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        if 'profile_picture' in validated_data:
            profile_picture = validated_data['profile_picture']
            if profile_picture:
                self.validate_profile_picture(profile_picture)
                
        return super().update(instance, validated_data)
    
    def get_profile_picture_url(self, obj):
        if obj.profile_picture:
            return obj.profile_picture.url
        return None

class MentorListSerializer(serializers.ModelSerializer):
    """Serializer for listing available mentors"""
    name = serializers.CharField(source='mentors_profile.name')
    bio = serializers.CharField(source='mentors_profile.bio')
    expertise_tags = serializers.JSONField(source='mentors_profile.expertise_tags')
    years_of_experience = serializers.IntegerField(source='mentors_profile.years_of_experience')
    profile_picture_url = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'name', 'bio', 'expertise_tags', 'years_of_experience', 'profile_picture_url']
    
    def get_profile_picture_url(self, obj):
        if hasattr(obj, 'mentors_profile') and obj.mentors_profile.profile_picture:
            return obj.mentors_profile.profile_picture.url
        return None

class FileValidationMixin:
    """Mixin for validating file uploads"""
    
    def validate_file(self, file):
        if not file:
            return file
            
        # Validate file size (5MB max)
        if file.size > 5 * 1024 * 1024:  # 5MB in bytes
            raise serializers.ValidationError("File size exceeds 5MB limit.")
            
        # Validate file type
        mime = magic.Magic(mime=True)
        file_type = mime.from_buffer(file.read())
        file.seek(0)  # Reset file pointer after reading
        
        valid_types = [
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'text/plain',
            'text/csv',
            'image/jpeg',
            'image/png', 
            'image/gif'
        ]
        
        if file_type not in valid_types:
            raise serializers.ValidationError(
                "Invalid file format. Supported formats: PDF, DOCX, XLSX, PPTX, TXT, CSV, PNG, JPEG, GIF."
            )
            
        return file

class MessageSerializer(serializers.ModelSerializer, FileValidationMixin):
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    receiver_username = serializers.CharField(source='receiver.username', read_only=True)
    file_url = serializers.CharField(read_only=True)
    
    class Meta:
        model = Message
        fields = ['id', 'sender', 'receiver', 'sender_username', 'receiver_username', 
                  'content', 'file', 'file_url', 'timestamp']
        read_only_fields = ['sender', 'timestamp']
        
    def validate(self, attrs):
        # Ensure either content or file is provided
        if not attrs.get('content') and not attrs.get('file'):
            raise serializers.ValidationError("Either content or file must be provided.")
        return attrs

class MentorshipRequestSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.students_profile.name', read_only=True)
    mentor_name = serializers.CharField(source='mentor.mentors_profile.name', read_only=True)
    student_details = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = MentorshipRequest
        fields = ['id', 'student', 'mentor', 'student_name', 'mentor_name', 
                  'goal', 'message', 'status', 'rejection_reason', 'created_at', 'updated_at', 'student_details']
        read_only_fields = ['status', 'rejection_reason', 'created_at', 'updated_at']
        extra_kwargs = {
            'message': {'write_only': False, 'required': False},
        }
    
    def get_student_details(self, obj):
        """Get detailed information about the student including their projects"""
        if self.context.get('include_student_details', False):
            return StudentProfileSerializer(obj.student.students_profile).data
        return None
    
    def validate(self, data):
        student = data['student']
        mentor = data['mentor']
        
        # Check that the student is actually a student
        if not hasattr(student, 'students_profile'):
            raise serializers.ValidationError("User is not a student")
        
        # Check that the mentor is actually a mentor
        if not hasattr(mentor, 'mentors_profile'):
            raise serializers.ValidationError("User is not a mentor")
        
        # Check if student already has an active request
        active_requests = MentorshipRequest.objects.filter(
            student=student,
            status__in=['pending', 'accepted']
        )
        
        if self.instance:  # Updating an existing instance
            active_requests = active_requests.exclude(id=self.instance.id)
        
        if active_requests.exists():
            raise serializers.ValidationError(
                "You already have an active mentorship request. Please wait for a response or cancel your existing request."
            )
        
        return data
    
    def create(self, validated_data):
        # Ensure the student is the current user
        validated_data['student'] = self.context['request'].user
        return super().create(validated_data)
