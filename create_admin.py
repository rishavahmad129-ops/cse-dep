from app import app, db
from models import Admin
from werkzeug.security import generate_password_hash

def setup_admin():
    with app.app_context():
        # Check if admin already exists
        if Admin.query.filter_by(username='admin').first():
            print("Admin user already exists.")
            return

        # Create new admin
        hashed_pw = generate_password_hash('admin123') # Change this password!
        new_admin = Admin(username='admin', password_hash=hashed_pw)
        
        db.session.add(new_admin)
        db.session.commit()
        print("Admin account created successfully! Username: admin | Password: admin123")

if __name__ == '__main__':
    setup_admin()