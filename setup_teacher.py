from app import app, db
from models import Teacher, TeacherLogin
from werkzeug.security import generate_password_hash

with app.app_context():
    # Clear existing
    TeacherLogin.query.delete()
    Teacher.query.delete()
    db.session.commit()
    
    # Create teacher
    teacher = Teacher(
        first_name='John',
        last_name='Sokwayo',
        email='sokwayo@gmail.com',
        phone='0722123456',
        class_name='Form 1A',
        subject='Mathematics',
        qualification='B.Ed',
        avatar_url=None
    )
    db.session.add(teacher)
    db.session.flush()  # Get ID
    
    # Create login
    login = TeacherLogin(
        teacher_id=teacher.id,
        username='sokwayo@gmail.com',
        password_hash=generate_password_hash('okwayo123')
    )
    db.session.add(login)
    db.session.commit()
    
    print(f"Created Teacher ID {teacher.id}: {teacher.name}")
    print("Login: sokwayo@gmail.com / okwayo123")
    print("Ready for testing!")
