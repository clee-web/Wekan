from app import app, db
from models import Student

def remove_homabay_students():
    with app.app_context():
        try:
            # Find all students with residence containing 'homabay' (case insensitive)
            homabay_students = Student.query.filter(
                Student.residence.ilike('%homabay%')
            ).all()
            
            count = len(homabay_students)
            
            if count == 0:
                print("No students found with residence containing 'homabay'")
                return
                
            # Display students that will be deleted
            print(f"Found {count} students with residence containing 'homabay':")
            for student in homabay_students[:5]:  # Show first 5 as examples
                print(f"- ID: {student.id}, Name: {student.name}, Residence: {student.residence}")
                
            if count > 5:
                print(f"... and {count - 5} more")
                
            # Ask for confirmation
            confirm = input("\nDo you want to delete these students? This action cannot be undone. (yes/no): ")
            
            if confirm.lower() == 'yes':
                # Delete the students
                for student in homabay_students:
                    db.session.delete(student)
                
                db.session.commit()
                print(f"\n✅ Successfully deleted {count} students with residence containing 'homabay'")
            else:
                print("\nOperation cancelled.")
                
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ An error occurred: {str(e)}")
            print("No changes were made to the database.")

if __name__ == '__main__':
    remove_homabay_students()
