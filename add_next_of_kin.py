from app import app, db
from models import Student
with app.app_context():
    # Add column if not exists (SQLite)
    try:
        db.engine.execute('ALTER TABLE student ADD COLUMN next_of_kin VARCHAR(100)')
        print("Added next_of_kin column to student table")
    except Exception as e:
        print(f"Column may already exist or error: {e}")
    
    # Update existing students with empty string
    students = Student.query.all()
    updated = 0
    for student in students:
        if not hasattr(student, 'next_of_kin') or student.next_of_kin is None:
            student.next_of_kin = ''
            updated += 1
    db.session.commit()
    print(f"Updated {updated} existing students with empty next_of_kin")

