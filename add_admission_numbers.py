from app import app, db
from models import Student
from sqlalchemy import text

def add_admission_numbers():
    with app.app_context():
        try:
            # Check if the column exists
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            columns = [column['name'] for column in inspector.get_columns('student')]
            
            if 'admission_number' not in columns:
                print("Adding admission_number column...")
                # Add the column
                with db.engine.connect() as connection:
                    connection.execute(text('ALTER TABLE student ADD COLUMN admission_number VARCHAR(20)'))
                    connection.commit()
                
                # Generate admission numbers for existing students
                print("Generating admission numbers...")
                students = Student.query.order_by(Student.id).all()
                for i, student in enumerate(students, 1):
                    student.admission_number = f'ADM-{i:04d}'
                
                db.session.commit()
                
                # Add UNIQUE constraint
                print("Adding UNIQUE constraint...")
                with db.engine.connect() as connection:
                    connection.execute(text('CREATE UNIQUE INDEX IF NOT EXISTS idx_student_admission_number ON student(admission_number)'))
                    connection.commit()
                
                print("Successfully added admission numbers to all students!")
            else:
                print("admission_number column already exists.")
                
                # Check if we need to generate admission numbers
                if Student.query.filter(Student.admission_number.is_(None)).count() > 0:
                    print("Generating admission numbers for new students...")
                    students = Student.query.filter(Student.admission_number.is_(None)).order_by(Student.id).all()
                    max_id = db.session.query(db.func.max(Student.id)).scalar() or 0
                    for i, student in enumerate(students, max_id + 1):
                        student.admission_number = f'ADM-{i:04d}'
                    db.session.commit()
                    print(f"Generated admission numbers for {len(students)} students.")
                else:
                    print("All students already have admission numbers.")
                    
        except Exception as e:
            db.session.rollback()
            print(f"An error occurred: {str(e)}")
            raise

if __name__ == '__main__':
    add_admission_numbers()
