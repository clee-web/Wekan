from app import app, db
from models import Student

def mark_session_inactive(session_number):
    with app.app_context():
        try:
            # Update all active students in the specified session to inactive
            updated_count = db.session.query(Student).filter(
                Student.session == str(session_number),
                Student.active == True
            ).update({'active': False}, synchronize_session=False)
            
            db.session.commit()
            print(f'Successfully marked {updated_count} students from session {session_number} as inactive')
            return updated_count
        except Exception as e:
            db.session.rollback()
            print(f'Error marking session {session_number} as inactive: {str(e)}')
            return 0

if __name__ == '__main__':
    session_number = input("Enter session number to mark as inactive: ")
    confirm = input(f"Are you sure you want to mark all active students in session {session_number} as inactive? (yes/no): ")
    
    if confirm.lower() == 'yes':
        count = mark_session_inactive(session_number)
        print(f"Marked {count} students as inactive in session {session_number}")
    else:
        print("Operation cancelled.")
