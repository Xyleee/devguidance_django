# DevGuidance Project - Entity Relationship Diagram (ERD)

## Database Schema Overview

This ERD represents the database schema for the DevGuidance mentorship platform, showing the relationships between users, profiles, projects, mentorship requests, and messages.

## Entities and Relationships

### 1. User (Django Built-in)
**Primary Key:** id (Integer, Auto-increment)
- username (CharField, unique)
- email (EmailField, unique)
- first_name (CharField)
- last_name (CharField)
- password (CharField, hashed)
- is_active (BooleanField)
- is_staff (BooleanField)
- is_superuser (BooleanField)
- date_joined (DateTimeField)
- last_login (DateTimeField)

### 2. StudentProfile
**Primary Key:** id (Integer, Auto-increment)
**Foreign Key:** user_id → User.id (OneToOne)
- name (CharField, max_length=100)
- bio (TextField, optional)
- year_level (IntegerField, default=1)
- tech_stack (JSONField, list of technologies)
- photo (ImageField, optional, upload_to=profile_photos/student/)
- created_at (DateTimeField, auto_now_add)
- updated_at (DateTimeField, auto_now)

### 3. StudentProject
**Primary Key:** id (Integer, Auto-increment)
**Foreign Key:** student_id → StudentProfile.id (ForeignKey)
- title (CharField, max_length=100)
- description (TextField)
- tools_used (JSONField, list of tools)
- created_at (DateTimeField, auto_now_add)
- updated_at (DateTimeField, auto_now)

### 4. MentorProfile
**Primary Key:** id (Integer, Auto-increment)
**Foreign Key:** user_id → User.id (OneToOne)
- name (CharField, max_length=100)
- bio (TextField, optional)
- experience_years (IntegerField, default=0)
- expertise_tags (JSONField, list of expertise areas)
- photo (ImageField, optional, upload_to=profile_photos/mentor/)
- created_at (DateTimeField, auto_now_add)
- updated_at (DateTimeField, auto_now)

### 5. MentorshipRequest
**Primary Key:** id (Integer, Auto-increment)
**Foreign Key:** student_id → User.id (ForeignKey, related_name='sent_requests')
**Foreign Key:** mentor_id → User.id (ForeignKey, related_name='received_requests')
- status (CharField, choices=['pending', 'accepted', 'declined'], default='pending')
- message (TextField, optional, student's request message)
- rejection_reason (TextField, optional, mentor's rejection reason)
- created_at (DateTimeField, auto_now_add)
- updated_at (DateTimeField, auto_now)

**Constraints:**
- UniqueConstraint: (student, mentor) WHERE status IN ('pending', 'accepted')

### 6. Message
**Primary Key:** id (Integer, Auto-increment)
**Foreign Key:** sender_id → User.id (ForeignKey, related_name='sent_messages')
**Foreign Key:** receiver_id → User.id (ForeignKey, related_name='received_messages')
- content (TextField, optional)
- file (FileField, optional, upload_to=message_files/)
- timestamp (DateTimeField, auto_now_add)
- is_read (BooleanField, default=False)

## Relationship Types

### One-to-One Relationships
1. **User ↔ StudentProfile**: Each user can have one student profile
2. **User ↔ MentorProfile**: Each user can have one mentor profile

### One-to-Many Relationships
1. **StudentProfile → StudentProject**: One student can have multiple projects
2. **User → MentorshipRequest (as student)**: One user can send multiple mentorship requests
3. **User → MentorshipRequest (as mentor)**: One user can receive multiple mentorship requests
4. **User → Message (as sender)**: One user can send multiple messages
5. **User → Message (as receiver)**: One user can receive multiple messages

### Many-to-Many Relationships
- **Implicit through MentorshipRequest**: Students and Mentors have a many-to-many relationship through mentorship requests

## Business Rules

1. **User Types**: A user can be either a student OR a mentor (not both)
2. **Mentorship Constraints**: 
   - A student can only have one active mentorship request to the same mentor
   - When a mentorship request is accepted, all other pending requests from that student are declined
3. **File Uploads**:
   - Profile photos are automatically cropped to 1:1 aspect ratio
   - Message files support multiple formats (PDF, DOCX, images, etc.)
4. **Authentication**: JWT-based authentication with access and refresh tokens

## Indexing Strategy

### Recommended Indexes
1. **User.username** (unique index - already created by Django)
2. **User.email** (unique index - already created by Django)
3. **MentorshipRequest.status** (for filtering by status)
4. **MentorshipRequest.student, MentorshipRequest.mentor** (composite index for unique constraint)
5. **Message.timestamp** (for ordering messages)
6. **Message.sender, Message.receiver** (for message history queries)

## ERD Visual Representation

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│      User       │    │  StudentProfile  │    │ StudentProject  │
├─────────────────┤    ├──────────────────┤    ├─────────────────┤
│ id (PK)         │◄──►│ id (PK)          │◄──┤ id (PK)         │
│ username        │    │ user_id (FK)     │   │ student_id (FK) │
│ email           │    │ name             │   │ title           │
│ first_name      │    │ bio              │   │ description     │
│ last_name       │    │ year_level       │   │ tools_used      │
│ password        │    │ tech_stack       │   │ created_at      │
│ is_active       │    │ photo            │   │ updated_at      │
│ is_staff        │    │ created_at       │   └─────────────────┘
│ is_superuser    │    │ updated_at       │
│ date_joined     │    └──────────────────┘
│ last_login      │
└─────────────────┘
        │
        │
        │
┌─────────────────┐    ┌──────────────────┐
│  MentorProfile  │    │ MentorshipRequest│
├─────────────────┤    ├──────────────────┤
│ id (PK)         │    │ id (PK)          │
│ user_id (FK)    │◄─┐ │ student_id (FK)  │◄─┐
│ name            │  │ │ mentor_id (FK)   │◄─┼─┐
│ bio             │  │ │ status           │  │ │
│ experience_years│  │ │ message          │  │ │
│ expertise_tags  │  │ │ rejection_reason │  │ │
│ photo           │  │ │ created_at       │  │ │
│ created_at      │  │ │ updated_at       │  │ │
│ updated_at      │  │ └──────────────────┘  │ │
└─────────────────┘  │                       │ │
                     │                       │ │
                     │    ┌─────────────────┐│ │
                     │    │    Message      ││ │
                     │    ├─────────────────┤│ │
                     │    │ id (PK)         ││ │
                     └────┤ sender_id (FK)  ││ │
                          │ receiver_id (FK)├┘ │
                          │ content         │  │
                          │ file            │  │
                          │ timestamp       │  │
                          │ is_read         │  │
                          └─────────────────┘  │
                                               │
                          ┌──────────────────┐ │
                          │      User        │ │
                          │   (Reference)    │◄┘
                          └──────────────────┘
```

## Database Normalization

The schema follows **Third Normal Form (3NF)**:

1. **1NF**: All tables have atomic values and unique rows
2. **2NF**: All non-key attributes are fully dependent on primary keys
3. **3NF**: No transitive dependencies exist

### Normalization Benefits
- Eliminates data redundancy
- Ensures data integrity
- Supports efficient queries
- Maintains referential integrity through foreign key constraints

## Performance Considerations

1. **JSON Fields**: Used for `tech_stack`, `tools_used`, and `expertise_tags` for flexibility
2. **File Storage**: Images and files stored on filesystem with database paths
3. **Cascade Deletes**: Proper cascade relationships prevent orphaned records
4. **Unique Constraints**: Prevent duplicate mentorship requests and ensure data integrity

This ERD provides a comprehensive view of the DevGuidance platform's data architecture, supporting the mentorship ecosystem between students and mentors. 