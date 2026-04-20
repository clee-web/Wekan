from app import app, db
from models import Student

def update_database():
    with app.app_context():
        try:
            # Check if the column already exists
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            columns = [column['name'] for column in inspector.get_columns('student')]
            
            if 'admission_number' not in columns:
                print("Adding admission_number column to student table...")
                
                # Add the column without UNIQUE constraint first
                db.engine.execute('ALTER TABLE student ADD COLUMN admission_number VARCHAR(20)')
                
                # Generate admission numbers for existing students
                print("Generating admission numbers for existing students...")
                students = Student.query.all()
                for i, student in enumerate(students, 1):
                    student.admission_number = f'ADM-{i:04d}'
                
                db.session.commit()
                
                # Now add the UNIQUE constraint
                print("Adding UNIQUE constraint to admission_number...")
                db.engine.execute('CREATE UNIQUE INDEX idx_student_admission_number ON student(admission_number)')
                
                print("Successfully updated database schema and populated admission numbers.")
            else:
                print("admission_number column already exists.")
                
        except Exception as e:
            db.session.rollback()
            print(f"An error occurred: {str(e)}")
            raise

if __name__ == '__main__':
    update_database()
