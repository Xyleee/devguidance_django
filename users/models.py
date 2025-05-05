from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    name = models.CharField(max_length=100)
    bio = models.TextField(blank=True)
    year_level = models.IntegerField(default=1)
    tech_stack = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

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
