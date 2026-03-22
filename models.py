from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

class Faculty(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    designation = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    specialization = db.Column(db.String(200))
    image_path = db.Column(db.String(255), nullable=True)


class Notice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    is_highlight = db.Column(db.Boolean, default=False)
    pdf_file = db.Column(db.String(255), nullable=True)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    event_date = db.Column(db.DateTime, nullable=False)
    description = db.Column(db.Text)
    location = db.Column(db.String(150))

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    enrollment_no = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    batch_year = db.Column(db.Integer, nullable=False)

# Add this class below your existing models
class DepartmentInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    about_text = db.Column(db.Text, nullable=False, default="Welcome to the Department of Computer Science & Engineering.")
    vision = db.Column(db.Text, default="To be a center of excellence in computer science education and research.")
    mission = db.Column(db.Text, default="To produce globally competent and socially responsible computer engineers.")
    
    # Updated HOD Details
    hod_name = db.Column(db.String(100), nullable=True)
    hod_message = db.Column(db.Text, nullable=True)
    hod_image = db.Column(db.String(255), nullable=True) # NEW
    
    # NEW: Principal Details
    principal_name = db.Column(db.String(100), nullable=True)
    principal_message = db.Column(db.Text, nullable=True)
    principal_image = db.Column(db.String(255), nullable=True)
    
    contact_email = db.Column(db.String(120), nullable=True)
    contact_phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.Text, nullable=True) 


class Gallery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    media_type = db.Column(db.String(20), nullable=False) # 'image' or 'video'
    file_path = db.Column(db.String(255), nullable=False) # Local filename or YouTube URL
    date_added = db.Column(db.DateTime, server_default=db.func.now())

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String(20), unique=True, nullable=False)
    title = db.Column(db.String(150), nullable=False)
    credits = db.Column(db.Integer, nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    
    # Link to the Faculty table
    faculty_id = db.Column(db.Integer, db.ForeignKey('faculty.id'), nullable=True)
    
    # Create a relationship so we can easily call course.professor.name in our templates
    professor = db.relationship('Faculty', backref=db.backref('courses', lazy=True))    

class HeroBanner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_path = db.Column(db.String(255), nullable=False)
    heading = db.Column(db.String(200), nullable=True)
    subheading = db.Column(db.String(500), nullable=True)
    date_added = db.Column(db.DateTime, server_default=db.func.now())


