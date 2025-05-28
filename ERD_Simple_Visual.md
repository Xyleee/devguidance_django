# DevGuidance ERD - Visual Representation

## Entity Relationship Diagram (Mermaid Format)

```mermaid
erDiagram
    User {
        int id PK
        string username UK
        string email UK
        string first_name
        string last_name
        string password
        boolean is_active
        boolean is_staff
        datetime date_joined
        datetime last_login
    }
    
    StudentProfile {
        int id PK
        int user_id FK
        string name
        text bio
        int year_level
        json tech_stack
        string photo
        datetime created_at
        datetime updated_at
    }
    
    StudentProject {
        int id PK
        int student_id FK
        string title
        text description
        json tools_used
        datetime created_at
        datetime updated_at
    }
    
    MentorProfile {
        int id PK
        int user_id FK
        string name
        text bio
        int experience_years
        json expertise_tags
        string photo
        datetime created_at
        datetime updated_at
    }
    
    MentorshipRequest {
        int id PK
        int student_id FK
        int mentor_id FK
        string status
        text message
        text rejection_reason
        datetime created_at
        datetime updated_at
    }
    
    Message {
        int id PK
        int sender_id FK
        int receiver_id FK
        text content
        string file
        datetime timestamp
        boolean is_read
    }

    %% Relationships
    User ||--o| StudentProfile : "has one (optional)"
    User ||--o| MentorProfile : "has one (optional)"
    StudentProfile ||--o{ StudentProject : "has many"
    User ||--o{ MentorshipRequest : "sends as student"
    User ||--o{ MentorshipRequest : "receives as mentor"
    User ||--o{ Message : "sends"
    User ||--o{ Message : "receives"
```

## Database Schema Summary

### Primary Entities
- **User**: Core authentication and user data (Django built-in)
- **StudentProfile**: Student-specific information and preferences
- **MentorProfile**: Mentor-specific information and expertise
- **StudentProject**: Projects created by students
- **MentorshipRequest**: Requests for mentorship between students and mentors
- **Message**: Communication between users

### Key Relationships
1. **User ↔ StudentProfile**: One-to-One (optional)
2. **User ↔ MentorProfile**: One-to-One (optional)
3. **StudentProfile → StudentProject**: One-to-Many
4. **User → MentorshipRequest**: One-to-Many (as both student and mentor)
5. **User → Message**: One-to-Many (as both sender and receiver)

### Business Rules
- A user can be either a Student OR Mentor (not both)
- Students can have multiple projects
- Students can send multiple mentorship requests
- Mentors can receive multiple mentorship requests
- Only one active mentorship per student-mentor pair
- Real-time messaging between connected users

### Data Types Used
- **JSON Fields**: For flexible data like tech_stack, tools_used, expertise_tags
- **ImageField**: For profile photos with automatic processing
- **FileField**: For message attachments with validation
- **DateTime**: For timestamps and audit trails
- **Constraints**: Unique constraints prevent duplicate active mentorships

This ERD represents a normalized, scalable database design that supports the complete mentorship platform workflow. 