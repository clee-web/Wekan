from app import app, db
from models import Teacher, TeacherLogin
from werkzeug.security import generate_password_hash

with app.app_context():
    # Create a test teacher
    teacher = Teacher(
        name="Test Teacher",
        phone="1234567890",
        email="test.teacher@example.com",
        qualification="B.Ed",
        subject="Mathematics"
    )
    
    # Add teacher to database
    db.session.add(teacher)
    db.session.commit()
    
    # Create login credentials
    login = TeacherLogin(
        teacher_id=teacher.id,
        username="testteacher",
        password_hash=generate_password_hash("password123")
    )
    
    # Add login to database
    db.session.add(login)
    db.session.commit()
    
    print(f"Teacher ID: {teacher.id}")
    print(f"Username: testteacher")
    print("Password: password123")
