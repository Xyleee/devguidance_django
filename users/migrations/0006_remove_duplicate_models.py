# Generated manually to fix conflicting models
from django.db import migrations

class Migration(migrations.Migration):
    
    dependencies = [
        ('users', '0005_message_is_read'),
    ]
    
    operations = [
        # Remove StudentProject model first (has foreign key to StudentProfile)
        migrations.DeleteModel(
            name='StudentProject',
        ),
        # Remove MentorshipRequest model 
        migrations.DeleteModel(
            name='MentorshipRequest',
        ),
        # Remove StudentProfile model (conflicts with students app)
        migrations.DeleteModel(
            name='StudentProfile',
        ),
        # Remove MentorProfile model (conflicts with mentors app)
        migrations.DeleteModel(
            name='MentorProfile',
        ),
    ] 