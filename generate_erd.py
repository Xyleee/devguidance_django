#!/usr/bin/env python3
"""
Script to generate ERD for DevGuidance Django project
This creates a visual representation of the database schema
"""

import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'devguidance_django.settings')
django.setup()

from django.apps import apps
from django.db import models
import graphviz

def generate_erd():
    """Generate ERD diagram for the DevGuidance project"""
    
    # Create a new directed graph
    dot = graphviz.Digraph(comment='DevGuidance ERD')
    dot.attr(rankdir='TB', size='12,8')
    dot.attr('node', shape='record', fontsize='10')
    
    # Define our main models
    model_info = {
        'User': {
            'fields': [
                'id (PK)',
                'username',
                'email', 
                'first_name',
                'last_name',
                'password',
                'is_active',
                'is_staff',
                'date_joined'
            ],
            'color': '#E3F2FD'  # Light blue
        },
        'StudentProfile': {
            'fields': [
                'id (PK)',
                'user_id (FK → User)',
                'name',
                'bio',
                'year_level',
                'tech_stack (JSON)',
                'photo',
                'created_at',
                'updated_at'
            ],
            'color': '#E8F5E8'  # Light green
        },
        'StudentProject': {
            'fields': [
                'id (PK)',
                'student_id (FK → StudentProfile)',
                'title',
                'description',
                'tools_used (JSON)',
                'created_at',
                'updated_at'
            ],
            'color': '#FFF3E0'  # Light orange
        },
        'MentorProfile': {
            'fields': [
                'id (PK)',
                'user_id (FK → User)',
                'name',
                'bio',
                'experience_years',
                'expertise_tags (JSON)',
                'photo',
                'created_at',
                'updated_at'
            ],
            'color': '#F3E5F5'  # Light purple
        },
        'MentorshipRequest': {
            'fields': [
                'id (PK)',
                'student_id (FK → User)',
                'mentor_id (FK → User)',
                'status',
                'message',
                'rejection_reason',
                'created_at',
                'updated_at'
            ],
            'color': '#FFEBEE'  # Light red
        },
        'Message': {
            'fields': [
                'id (PK)',
                'sender_id (FK → User)',
                'receiver_id (FK → User)',
                'content',
                'file',
                'timestamp',
                'is_read'
            ],
            'color': '#F1F8E9'  # Light lime
        }
    }
    
    # Add nodes for each model
    for model_name, info in model_info.items():
        fields_str = '\\l'.join(info['fields']) + '\\l'
        
        dot.node(
            model_name,
            f'{{{model_name}|{fields_str}}}',
            style='filled',
            fillcolor=info['color']
        )
    
    # Define relationships
    relationships = [
        # One-to-One relationships
        ('User', 'StudentProfile', 'one_to_one'),
        ('User', 'MentorProfile', 'one_to_one'),
        
        # One-to-Many relationships
        ('StudentProfile', 'StudentProject', 'one_to_many'),
        ('User', 'MentorshipRequest', 'student_requests'),
        ('User', 'MentorshipRequest', 'mentor_requests'),
        ('User', 'Message', 'sent_messages'),
        ('User', 'Message', 'received_messages'),
    ]
    
    # Add edges for relationships
    for source, target, relationship_type in relationships:
        if relationship_type == 'one_to_one':
            dot.edge(source, target, label='1:1', color='blue', style='solid')
        elif relationship_type == 'one_to_many':
            dot.edge(source, target, label='1:M', color='red', style='solid')
        elif relationship_type == 'student_requests':
            dot.edge(source, target, label='student\\nrequests', color='green', style='dashed')
        elif relationship_type == 'mentor_requests':
            dot.edge(source, target, label='mentor\\nrequests', color='green', style='dashed')
        elif relationship_type == 'sent_messages':
            dot.edge(source, target, label='sends', color='purple', style='dotted')
        elif relationship_type == 'received_messages':
            dot.edge(source, target, label='receives', color='purple', style='dotted')
    
    # Add title
    dot.attr(label='DevGuidance Mentorship Platform\\nEntity Relationship Diagram')
    dot.attr(fontsize='16')
    
    # Add legend
    with dot.subgraph(name='cluster_legend') as legend:
        legend.attr(label='Legend')
        legend.attr(style='filled', color='lightgrey')
        
        legend.node('legend_oto', '1:1 = One-to-One', shape='plaintext')
        legend.node('legend_otm', '1:M = One-to-Many', shape='plaintext')
        legend.node('legend_fk', 'FK = Foreign Key', shape='plaintext')
        legend.node('legend_pk', 'PK = Primary Key', shape='plaintext')
    
    return dot

def save_erd():
    """Generate and save the ERD diagram"""
    try:
        erd = generate_erd()
        
        # Save as PNG
        erd.render('devguidance_erd', format='png', cleanup=True)
        print("✅ ERD generated successfully as 'devguidance_erd.png'")
        
        # Save as SVG for better quality
        erd.render('devguidance_erd', format='svg', cleanup=True)
        print("✅ ERD generated successfully as 'devguidance_erd.svg'")
        
        # Save source code
        with open('devguidance_erd.dot', 'w') as f:
            f.write(erd.source)
        print("✅ ERD source saved as 'devguidance_erd.dot'")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating ERD: {e}")
        return False

if __name__ == '__main__':
    print("🎨 Generating ERD for DevGuidance project...")
    success = save_erd()
    
    if success:
        print("\n📊 ERD files generated:")
        print("   - devguidance_erd.png (image)")
        print("   - devguidance_erd.svg (vector)")
        print("   - devguidance_erd.dot (source)")
        print("   - ERD.md (documentation)")
    else:
        print("\n❌ Failed to generate ERD. Make sure you have graphviz installed:")
        print("   pip install graphviz")
        print("   # Also install graphviz system package:")
        print("   # Windows: choco install graphviz")
        print("   # Mac: brew install graphviz") 
        print("   # Ubuntu: sudo apt-get install graphviz") 