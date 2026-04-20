from app import app, db
from models import Student

def update_student_active_status():
    with app.app_context():
        # Update students in sessions 1-4 to inactive
        older_students = Student.query.filter(
            Student.session.in_(['1', '2', '3', '4'])
        ).all()
        
        for student in older_students:
            student.active = False
        
        # Update students in sessions 5-6 to active
        current_students = Student.query.filter(
            Student.session.in_(['5', '6'])
        ).all()
        
        for student in current_students:
            student.active = True
            
        # Commit all changes
        db.session.commit()
        
        # Print summary
        print("\nStudent Status Update Summary:")
        print("-" * 30)
        
        # Count inactive students by session
        for session in ['1', '2', '3', '4']:
            count = Student.query.filter_by(session=session, active=False).count()
            print(f"Session {session}: {count} students marked inactive")
            
        # Count active students by session
        for session in ['5', '6']:
            count = Student.query.filter_by(session=session, active=True).count()
            print(f"Session {session}: {count} students marked active")

if __name__ == '__main__':
    update_student_active_status()
    print("\nDone! Student active status has been updated.")
