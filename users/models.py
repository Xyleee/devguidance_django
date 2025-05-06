from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
import uuid
import os

def upload_profile_photo(instance, filename):
    """Custom function to upload profile photos to specific paths with unique filenames"""
    # Get file extension
    ext = filename.split('.')[-1]
    # Generate a unique filename
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    # Return the upload path
    user_type = 'student' if hasattr(instance, 'student_profile') else 'mentor'
    return os.path.join('profile_photos', user_type, unique_filename)

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    name = models.CharField(max_length=100)
    bio = models.TextField(blank=True)
    year_level = models.IntegerField(default=1)
    tech_stack = models.JSONField(default=list)
    photo = models.ImageField(upload_to=upload_profile_photo, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Only process image if it's provided and being modified
        if self.photo and (not self.pk or StudentProfile.objects.get(pk=self.pk).photo != self.photo):
            self._crop_and_resize_image()
        super().save(*args, **kwargs)
    
    def _crop_and_resize_image(self):
        """Crop and resize the profile photo to 1:1 aspect ratio"""
        if not self.photo:
            return
        
        # Open the image
        img = Image.open(self.photo)
        
        # Convert to RGB if necessary
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Get the current dimensions
        width, height = img.size
        
        # Determine the size for the square crop (use the smaller dimension)
        size = min(width, height)
        
        # Calculate coordinates for center crop
        left = (width - size) / 2
        top = (height - size) / 2
        right = (width + size) / 2
        bottom = (height + size) / 2
        
        # Crop the image to a square
        img = img.crop((left, top, right, bottom))
        
        # Resize to a standard size if needed (optional)
        # img = img.resize((300, 300), Image.LANCZOS)
        
        # Save the processed image
        output = BytesIO()
        img.save(output, format='JPEG', quality=85)
        output.seek(0)
        
        # Replace the image file with the processed one
        self.photo.save(
            self.photo.name,
            ContentFile(output.read()),
            save=False
        )

class StudentProject(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='projects')
    title = models.CharField(max_length=100)
    description = models.TextField()
    tools_used = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title

class MentorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='mentor_profile')
    name = models.CharField(max_length=100)
    bio = models.TextField(blank=True)
    experience_years = models.IntegerField(default=0)
    expertise_tags = models.JSONField(default=list)
    photo = models.ImageField(upload_to=upload_profile_photo, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Only process image if it's provided and being modified
        if self.photo and (not self.pk or MentorProfile.objects.get(pk=self.pk).photo != self.photo):
            self._crop_and_resize_image()
        super().save(*args, **kwargs)
    
    def _crop_and_resize_image(self):
        """Crop and resize the profile photo to 1:1 aspect ratio"""
        if not self.photo:
            return
        
        # Open the image
        img = Image.open(self.photo)
        
        # Convert to RGB if necessary
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Get the current dimensions
        width, height = img.size
        
        # Determine the size for the square crop (use the smaller dimension)
        size = min(width, height)
        
        # Calculate coordinates for center crop
        left = (width - size) / 2
        top = (height - size) / 2
        right = (width + size) / 2
        bottom = (height + size) / 2
        
        # Crop the image to a square
        img = img.crop((left, top, right, bottom))
        
        # Save the processed image
        output = BytesIO()
        img.save(output, format='JPEG', quality=85)
        output.seek(0)
        
        # Replace the image file with the processed one
        self.photo.save(
            self.photo.name,
            ContentFile(output.read()),
            save=False
        )

class MentorshipRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
    )
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_requests')
    mentor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_requests')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    message = models.TextField(blank=True, help_text="Student's reason for requesting mentorship")
    rejection_reason = models.TextField(blank=True, help_text="Mentor's reason for declining the request")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        constraints = [
            # Ensure a student can only have one active request to a specific mentor
            models.UniqueConstraint(
                fields=['student', 'mentor'],
                condition=models.Q(status='pending') | models.Q(status='accepted'),
                name='unique_active_request'
            )
        ]
    
    def __str__(self):
        return f"{self.student.username}'s request to {self.mentor.username}"
    
    def save(self, *args, **kwargs):
        # If request is being accepted, decline all other pending requests from this student
        if self.status == 'accepted' and self._state.adding is False:
            MentorshipRequest.objects.filter(
                student=self.student,
                status='pending'
            ).exclude(id=self.id).update(status='declined')
        
        super().save(*args, **kwargs)

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField(blank=True)
    file = models.FileField(upload_to='message_files/', blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"Message from {self.sender.username} to {self.receiver.username}"
    
    @property
    def file_url(self):
        if self.file:
            return self.file.url
        return None
