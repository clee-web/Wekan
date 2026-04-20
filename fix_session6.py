from app import app, db
from models import Student

def fix_session6():
    with app.app_context():
        try:
            # First, check how many active students are in session 6
            active_count = Student.query.filter_by(session='6', active=True).count()
            print(f"Found {active_count} active students in session 6")
            
            # Mark all active students in session 6 as inactive
            result = db.session.query(Student).filter(
                Student.session == '6',
                Student.active == True
            ).update({'active': False}, synchronize_session=False)
            
            db.session.commit()
            print(f"Marked {result} students as inactive in session 6")
            
            # Verify the update
            remaining = Student.query.filter_by(session='6', active=True).count()
            print(f"After update, {remaining} active students remain in session 6")
            
            return result
            
        except Exception as e:
            db.session.rollback()
            print(f"Error: {str(e)}")
            return 0

if __name__ == '__main__':
    fix_session6()
