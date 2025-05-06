from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .models import StudentProfile, StudentProject, MentorProfile, MentorshipRequest, Message
from django.core.files.uploadedfile import UploadedFile
from django.core.exceptions import ValidationError
import os
import magic

class PhotoValidationMixin:
    """Mixin for validating photo uploads"""
    
    def validate_photo(self, photo):
        if not photo:
            return photo
            
        # Validate file size (2MB max)
        if photo.size > 2 * 1024 * 1024:  # 2MB in bytes
            raise serializers.ValidationError("Image file too large. Maximum size is 2MB.")
            
        # Validate file type
        mime = magic.Magic(mime=True)
        file_type = mime.from_buffer(photo.read())
        photo.seek(0)  # Reset file pointer after reading
        
        valid_types = ['image/jpeg', 'image/png', 'image/webp']
        if file_type not in valid_types:
            raise serializers.ValidationError(
                "Invalid image format. Only JPEG, PNG, and WebP are supported."
            )
            
        return photo

class RegisterSerializer(serializers.ModelSerializer, PhotoValidationMixin):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    user_type = serializers.ChoiceField(choices=['student', 'mentor'], required=True)
    name = serializers.CharField(required=True)
    photo = serializers.ImageField(required=False)
    
    class Meta:
        model = User
        fields = ('username', 'password', 'password2', 'email', 'first_name', 'last_name', 'user_type', 'name', 'photo')
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
        
        # Handle photo separately
        self.photo = None
        if 'photo' in attrs:
            self.photo = attrs.pop('photo')
            if self.photo:
                self.validate_photo(self.photo)
                
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
        
        # Add photo if provided
        if self.photo:
            profile.photo = self.photo
            profile.save()
            
        return user

class StudentProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProject
        fields = ['id', 'title', 'description', 'tools_used', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class StudentProfileSerializer(serializers.ModelSerializer, PhotoValidationMixin):
    projects = StudentProjectSerializer(many=True, read_only=True)
    photo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = StudentProfile
        fields = ['id', 'name', 'bio', 'year_level', 'tech_stack', 'projects', 'photo', 'photo_url', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
        extra_kwargs = {
            'photo': {'write_only': True}
        }
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        
        if 'photo' in validated_data:
            photo = validated_data['photo']
            if photo:
                self.validate_photo(photo)
                
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        if 'photo' in validated_data:
            photo = validated_data['photo']
            if photo:
                self.validate_photo(photo)
                
        return super().update(instance, validated_data)
    
    def get_photo_url(self, obj):
        if obj.photo:
            return obj.photo.url
        return None

class MentorProfileSerializer(serializers.ModelSerializer, PhotoValidationMixin):
    photo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = MentorProfile
        fields = ['id', 'name', 'bio', 'experience_years', 'expertise_tags', 'photo', 'photo_url', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
        extra_kwargs = {
            'photo': {'write_only': True}
        }
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        
        if 'photo' in validated_data:
            photo = validated_data['photo']
            if photo:
                self.validate_photo(photo)
                
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        if 'photo' in validated_data:
            photo = validated_data['photo']
            if photo:
                self.validate_photo(photo)
                
        return super().update(instance, validated_data)
    
    def get_photo_url(self, obj):
        if obj.photo:
            return obj.photo.url
        return None

class MentorListSerializer(serializers.ModelSerializer):
    """Serializer for listing available mentors"""
    name = serializers.CharField(source='mentor_profile.name')
    bio = serializers.CharField(source='mentor_profile.bio')
    expertise_tags = serializers.JSONField(source='mentor_profile.expertise_tags')
    experience_years = serializers.IntegerField(source='mentor_profile.experience_years')
    photo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'name', 'bio', 'expertise_tags', 'experience_years', 'photo_url']
    
    def get_photo_url(self, obj):
        if hasattr(obj, 'mentor_profile') and obj.mentor_profile.photo:
            return obj.mentor_profile.photo.url
        return None

class StudentProjectListSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProject
        fields = ['id', 'title', 'description', 'tools_used']

class StudentDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed student information with projects"""
    name = serializers.CharField(source='student_profile.name')
    bio = serializers.CharField(source='student_profile.bio')
    year_level = serializers.IntegerField(source='student_profile.year_level')
    tech_stack = serializers.JSONField(source='student_profile.tech_stack')
    projects = serializers.SerializerMethodField()
    photo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'name', 'bio', 'year_level', 'tech_stack', 'projects', 'photo_url']
    
    def get_projects(self, obj):
        student_profile = obj.student_profile
        projects = StudentProject.objects.filter(student=student_profile)
        return StudentProjectListSerializer(projects, many=True).data
    
    def get_photo_url(self, obj):
        if hasattr(obj, 'student_profile') and obj.student_profile.photo:
            return obj.student_profile.photo.url
        return None

class MentorshipRequestSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.student_profile.name', read_only=True)
    mentor_name = serializers.CharField(source='mentor.mentor_profile.name', read_only=True)
    student_details = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = MentorshipRequest
        fields = ['id', 'student', 'mentor', 'student_name', 'mentor_name', 
                  'status', 'message', 'rejection_reason', 'created_at', 'updated_at', 'student_details']
        read_only_fields = ['status', 'rejection_reason', 'created_at', 'updated_at']
        extra_kwargs = {
            'message': {'write_only': False, 'required': False},  # Allow message to be readable & writable
        }
    
    def get_student_details(self, obj):
        """Get detailed information about the student including their projects"""
        if self.context.get('include_student_details', False):
            return StudentDetailSerializer(obj.student).data
        return None
    
    def validate(self, data):
        student = data['student']
        mentor = data['mentor']
        
        # Check that the student is actually a student
        if not hasattr(student, 'student_profile'):
            raise serializers.ValidationError("User is not a student")
        
        # Check that the mentor is actually a mentor
        if not hasattr(mentor, 'mentor_profile'):
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

class FileValidationMixin:
    """Mixin for validating file uploads for messages"""
    
    def validate_file(self, file):
        if not file:
            return file
            
        # Validate file size (2MB max)
        if file.size > 2 * 1024 * 1024:  # 2MB in bytes
            raise serializers.ValidationError("File too large. Maximum size is 2MB.")
            
        # Validate file type
        mime = magic.Magic(mime=True)
        file_type = mime.from_buffer(file.read())
        file.seek(0)  # Reset file pointer after reading
        
        valid_types = [
            # Images
            'image/jpeg', 'image/png', 'image/webp', 'image/gif',
            # Documents
            'application/pdf', 'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain', 'application/rtf'
        ]
        
        if file_type not in valid_types:
            raise serializers.ValidationError(
                "Invalid file format. Supported formats: JPEG, PNG, WebP, GIF, PDF, DOC, DOCX, TXT, RTF."
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
            raise serializers.ValidationError("Either content or file must be provided")
            
        # Validate file if provided
        if file := attrs.get('file'):
            self.validate_file(file)
            
        return attrs
