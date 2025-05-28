from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save
from students.models import StudentProfile

class MentorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='mentors_profile')
    name = models.CharField(max_length=100)
    bio = models.TextField(blank=True)
    expertise_tags = models.JSONField(default=list)  # List of expertise areas
    years_of_experience = models.PositiveIntegerField(default=0)
    company = models.CharField(max_length=100, blank=True)
    position = models.CharField(max_length=100, blank=True)
    linkedin_profile = models.URLField(blank=True)
    github_profile = models.URLField(blank=True)
    profile_picture = models.ImageField(upload_to='mentor_pics/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Mentor Profile"

class MentorshipRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('completed', 'Completed'),
    ]
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mentorship_requests_sent')
    mentor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mentorship_requests_received')
    goal = models.TextField()
    message = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    rejection_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Mentorship Request: {self.student.username} -> {self.mentor.username}"
    
    def save(self, *args, **kwargs):
        # If this request is being accepted, decline all other pending requests from this student
        if self.status == 'accepted':
            MentorshipRequest.objects.filter(
                student=self.student,
                status='pending'
            ).exclude(id=self.id).update(
                status='declined',
                rejection_reason='Another mentor has accepted your request.'
            )
        
        super().save(*args, **kwargs)
