from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .models import StudentProfile, StudentProject, MentorProfile, MentorshipRequest, Message

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    user_type = serializers.ChoiceField(choices=['student', 'mentor'], required=True)
    name = serializers.CharField(required=True)
    
    class Meta:
        model = User
        fields = ('username', 'password', 'password2', 'email', 'first_name', 'last_name', 'user_type', 'name')
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
            StudentProfile.objects.create(
                user=user,
                name=self.name
            )
        elif self.user_type == 'mentor':
            MentorProfile.objects.create(
                user=user,
                name=self.name
            )
            
        return user

class StudentProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProject
        fields = ['id', 'title', 'description', 'tools_used', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class StudentProfileSerializer(serializers.ModelSerializer):
    projects = StudentProjectSerializer(many=True, read_only=True)
    
    class Meta:
        model = StudentProfile
        fields = ['id', 'name', 'bio', 'year_level', 'tech_stack', 'projects', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)

class MentorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MentorProfile
        fields = ['id', 'name', 'bio', 'experience_years', 'expertise_tags', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)

class MentorListSerializer(serializers.ModelSerializer):
    """Serializer for listing available mentors"""
    name = serializers.CharField(source='mentor_profile.name')
    bio = serializers.CharField(source='mentor_profile.bio')
    expertise_tags = serializers.JSONField(source='mentor_profile.expertise_tags')
    experience_years = serializers.IntegerField(source='mentor_profile.experience_years')
    
    class Meta:
        model = User
        fields = ['id', 'username', 'name', 'bio', 'expertise_tags', 'experience_years']


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
    
    class Meta:
        model = User
        fields = ['id', 'username', 'name', 'bio', 'year_level', 'tech_stack', 'projects']
    
    def get_projects(self, obj):
        student_profile = obj.student_profile
        projects = StudentProject.objects.filter(student=student_profile)
        return StudentProjectListSerializer(projects, many=True).data


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

class MessageSerializer(serializers.ModelSerializer):
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
        return attrs
