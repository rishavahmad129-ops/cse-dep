import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Faculty, Course, Notice, Event, Student, Admin, DepartmentInfo, Gallery, HeroBanner
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)

# --- Configuration ---
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///cse_dept.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# REQUIRED FOR SESSIONS: Set a strong secret key in production (.env)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback-secret-key-for-dev')

UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

db.init_app(app)

# Initialize database tables
with app.app_context():
    db.create_all()
    # Create default department info if it doesn't exist
    if not DepartmentInfo.query.first():
        default_info = DepartmentInfo()
        db.session.add(default_info)
        db.session.commit()

# --- Security Decorator ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            # If not logged in, send them back to the home page
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

# ==========================================
#          ADMIN AUTH ROUTES
# ==========================================

@app.route('/admin/login', methods=['POST'])
def admin_login():
    username = request.form.get('username')
    password = request.form.get('password')
    admin = Admin.query.filter_by(username=username).first()
    
    if admin and check_password_hash(admin.password_hash, password):
        session['admin_id'] = admin.id
        session['admin_username'] = admin.username
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('home'))

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_id', None)
    session.pop('admin_username', None)
    return redirect(url_for('home'))


# ==========================================
#       ADMIN DASHBOARD & CRUD ROUTES
# ==========================================

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    notices = Notice.query.order_by(Notice.date_posted.desc()).all()
    faculty = Faculty.query.all()
    info = DepartmentInfo.query.first()
    gallery_items = Gallery.query.order_by(Gallery.date_added.desc()).all()
    courses = Course.query.order_by(Course.semester.asc()).all() 
    events = Event.query.order_by(Event.event_date.desc()).all()
    
    # NEW: Fetch banners for the dashboard
    banners = HeroBanner.query.order_by(HeroBanner.date_added.desc()).all()
    
    stats = {
        'total_notices': len(notices),
        'total_faculty': len(faculty),
        'total_courses': len(courses),
        'total_events': len(events)
    }
    
    return render_template('admin_dashboard.html', 
                           notices=notices, faculty=faculty, stats=stats, 
                           info=info, gallery_items=gallery_items, 
                           courses=courses, events=events, banners=banners)



@app.route('/admin/settings/update', methods=['POST'])
@login_required
def update_settings():
    info = DepartmentInfo.query.first()
    
    info.about_text = request.form.get('about_text')
    info.vision = request.form.get('vision')
    info.mission = request.form.get('mission')
    info.hod_name = request.form.get('hod_name')
    info.hod_message = request.form.get('hod_message')
    info.principal_name = request.form.get('principal_name')
    info.principal_message = request.form.get('principal_message')
    info.contact_email = request.form.get('contact_email')
    info.contact_phone = request.form.get('contact_phone')
    info.address = request.form.get('address')
    
    # Handle HOD Image Upload
    hod_file = request.files.get('hod_image')
    if hod_file and allowed_file(hod_file.filename):
        filename = secure_filename(hod_file.filename)
        hod_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        info.hod_image = filename

    # Handle Principal Image Upload
    prin_file = request.files.get('principal_image')
    if prin_file and allowed_file(prin_file.filename):
        filename = secure_filename(prin_file.filename)
        prin_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        info.principal_image = filename
        
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/faculty/add', methods=['POST'])
@login_required
def add_faculty():
    name = request.form.get('name')
    designation = request.form.get('designation')
    email = request.form.get('email')
    specialization = request.form.get('specialization')
    
    # Handle Faculty Image Upload
    image_path = None
    file = request.files.get('image')
    if file and allowed_file(file.filename):
        image_path = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_path))
    
    if name and email:
        new_faculty = Faculty(
            name=name, 
            designation=designation, 
            email=email, 
            specialization=specialization,
            image_path=image_path
        )
        db.session.add(new_faculty)
        db.session.commit()
        
    return redirect(url_for('admin_dashboard'))



@app.route('/admin/notice/add', methods=['POST'])
@login_required
def add_notice():
    title = request.form.get('title')
    content = request.form.get('content')
    is_highlight = request.form.get('is_highlight') == 'on'
    
    # Handle the PDF upload
    pdf_filename = None
    file = request.files.get('pdf_file')
    if file and allowed_file(file.filename):
        pdf_filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename))
    
    if title and content:
        new_notice = Notice(title=title, content=content, is_highlight=is_highlight, pdf_file=pdf_filename)
        db.session.add(new_notice)
        db.session.commit()
        
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/notice/delete/<int:id>', methods=['POST'])
@login_required
def delete_notice(id):
    notice = Notice.query.get_or_404(id)
    
    # Delete the physical PDF file from the server if it exists
    if notice.pdf_file:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], notice.pdf_file)
        if os.path.exists(file_path):
            os.remove(file_path)
            
    db.session.delete(notice)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/gallery/add', methods=['POST'])
@login_required
def add_gallery_item():
    title = request.form.get('title')
    media_type = request.form.get('media_type')
    
    if media_type == 'image':
        file = request.files.get('file')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            new_item = Gallery(title=title, media_type='image', file_path=filename)
            db.session.add(new_item)
            db.session.commit()
            
    elif media_type == 'video':
        video_url = request.form.get('video_url')
        if video_url:
            if "youtube.com/watch?v=" in video_url:
                video_url = video_url.replace("watch?v=", "embed/")
            elif "youtu.be/" in video_url:
                video_url = video_url.replace("youtu.be/", "youtube.com/embed/")
            new_item = Gallery(title=title, media_type='video', file_path=video_url)
            db.session.add(new_item)
            db.session.commit()

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/gallery/delete/<int:id>', methods=['POST'])
@login_required
def delete_gallery_item(id):
    item = Gallery.query.get_or_404(id)
    if item.media_type == 'image':
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], item.file_path)
        if os.path.exists(file_path):
            os.remove(file_path)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/course/add', methods=['POST'])
@login_required
def add_course():
    course_code = request.form.get('course_code')
    title = request.form.get('title')
    credits = request.form.get('credits')
    semester = request.form.get('semester')
    faculty_id = request.form.get('faculty_id')
    
    if course_code and title:
        fac_id = int(faculty_id) if faculty_id else None
        new_course = Course(
            course_code=course_code, 
            title=title, 
            credits=int(credits), 
            semester=int(semester),
            faculty_id=fac_id
        )
        db.session.add(new_course)
        db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/course/delete/<int:id>', methods=['POST'])
@login_required
def delete_course(id):
    course = Course.query.get_or_404(id)
    db.session.delete(course)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

# --- Admin Faculty Routes ---


@app.route('/admin/faculty/delete/<int:id>', methods=['POST'])
@login_required
def delete_faculty(id):
    member = Faculty.query.get_or_404(id)
    db.session.delete(member)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))


# --- Admin Event Routes ---
@app.route('/admin/event/add', methods=['POST'])
@login_required
def add_event():
    title = request.form.get('title')
    event_date_str = request.form.get('event_date') # Comes from HTML datetime-local input
    description = request.form.get('description')
    location = request.form.get('location')
    
    if title and event_date_str:
        # Convert string from form into Python datetime object
        event_date = datetime.strptime(event_date_str, '%Y-%m-%dT%H:%M')
        
        new_event = Event(title=title, event_date=event_date, description=description, location=location)
        db.session.add(new_event)
        db.session.commit()
        
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/event/edit/<int:id>', methods=['POST'])
@login_required
def edit_event(id):
    event = Event.query.get_or_404(id)
    
    event.title = request.form.get('title')
    event.description = request.form.get('description')
    event.location = request.form.get('location')
    
    event_date_str = request.form.get('event_date')
    if event_date_str:
        event.event_date = datetime.strptime(event_date_str, '%Y-%m-%dT%H:%M')
        
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/event/delete/<int:id>', methods=['POST'])
@login_required
def delete_event(id):
    event = Event.query.get_or_404(id)
    db.session.delete(event)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))


# --- Admin Banner Routes ---
@app.route('/admin/banner/add', methods=['POST'])
@login_required
def add_banner():
    heading = request.form.get('heading')
    subheading = request.form.get('subheading')
    file = request.files.get('file')
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        new_banner = HeroBanner(image_path=filename, heading=heading, subheading=subheading)
        db.session.add(new_banner)
        db.session.commit()
        
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/banner/delete/<int:id>', methods=['POST'])
@login_required
def delete_banner(id):
    banner = HeroBanner.query.get_or_404(id)
    
    # Delete the physical image file
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], banner.image_path)
    if os.path.exists(file_path):
        os.remove(file_path)
        
    db.session.delete(banner)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

# ==========================================
#          PUBLIC FRONTEND ROUTES
# ==========================================

@app.route('/')
def home():
    recent_notices = Notice.query.order_by(Notice.date_posted.desc()).limit(3).all()
    upcoming_events = Event.query.order_by(Event.event_date.asc()).limit(2).all()
    
    # NEW: Fetch active banners
    banners = HeroBanner.query.order_by(HeroBanner.date_added.desc()).all()
    
    return render_template('index.html', notices=recent_notices, events=upcoming_events, banners=banners)

@app.route('/faculty')
def faculty():
    staff = Faculty.query.all()
    return render_template('faculty.html', faculty=staff)

@app.route('/courses')
def courses():
    all_courses = Course.query.order_by(Course.semester.asc()).all()
    return render_template('courses.html', courses=all_courses)

@app.route('/notices')
def notices():
    all_notices = Notice.query.order_by(Notice.date_posted.desc()).all()
    return render_template('notices.html', notices=all_notices)

@app.route('/events')
def events():
    all_events = Event.query.order_by(Event.event_date.desc()).all()
    return render_template('events.html', events=all_events)

@app.route('/research')
def research():
    return render_template('research.html')

@app.route('/about')
def about():
    info = DepartmentInfo.query.first()
    return render_template('about.html', info=info)

@app.route('/contact')
def contact():
    info = DepartmentInfo.query.first()
    return render_template('contact.html', info=info)

@app.route('/students')
def students():
    return render_template('students.html')

@app.route('/gallery')
def gallery():
    items = Gallery.query.order_by(Gallery.date_added.desc()).all()
    return render_template('gallery.html', items=items)

if __name__ == '__main__':
    app.run(debug=True, port=8080)