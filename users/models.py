from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone
import uuid
import os

def upload_message_file(instance, filename):
    """Custom function to upload message files to specific paths with unique filenames"""
    # Get file extension
    ext = filename.split('.')[-1]
    # Generate a unique filename
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    # Return the upload path
    return os.path.join('message_files', unique_filename)

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField(blank=True)
    file = models.FileField(upload_to=upload_message_file, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"Message from {self.sender.username} to {self.receiver.username}"
    
    @property
    def file_url(self):
        if self.file:
            return self.file.url
        return None 