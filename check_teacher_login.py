from models import TeacherLogin, db

# Create application context
from app import app
with app.app_context():
    # Query for the teacher login record
    login = TeacherLogin.query.filter_by(username='clee').first()
    if login:
        print(f"Found login record:")
        print(f"Username: {login.username}")
        print(f"Teacher ID: {login.teacher_id}")
        print(f"Password hash: {login.password_hash}")
        print(f"Created at: {login.created_at}")
    else:
        print("No login record found for username 'clee'")
