from app import app, db
from models import Student

print("Connecting to database...")
with app.app_context():
    try:
        # First, check how many active students are in session 6
        active_count = Student.query.filter_by(session='6', active=True).count()
        print(f"Found {active_count} active students in session 6")
        
        if active_count > 0:
            # Show some examples
            print("\nExample students to be marked inactive:")
            examples = Student.query.filter_by(session='6', active=True).limit(3).all()
            for student in examples:
                print(f"- ID: {student.id}, Name: {student.name}")
            
            # Ask for confirmation
            confirm = input("\nDo you want to mark these students as inactive? (yes/no): ")
            
            if confirm.lower() == 'yes':
                # Update all active students in session 6 to inactive
                result = db.session.query(Student).filter(
                    Student.session == '6',
                    Student.active == True
                ).update({'active': False}, synchronize_session=False)
                
                db.session.commit()
                print(f"\n✅ Successfully marked {result} students as inactive in session 6")
            else:
                print("\nOperation cancelled.")
        else:
            print("No active students found in session 6")
            
    except Exception as e:
        db.session.rollback()
        print(f"\n❌ Error: {str(e)}")
    
    input("\nPress Enter to exit...")
