from app import app, db
from models import Student
from sqlalchemy import text

def add_admission_column():
    with app.app_context():
        try:
            # Check if the column already exists
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            columns = [column['name'] for column in inspector.get_columns('student')]
            
            if 'admission_number' not in columns:
                # Add the column
                print("Adding admission_number column to student table...")
                with db.engine.connect() as connection:
                    connection.execute(text('ALTER TABLE student ADD COLUMN admission_number VARCHAR(20) UNIQUE'))
                    connection.commit()
                
                # Generate admission numbers for existing students
                print("Generating admission numbers for existing students...")
                students = Student.query.all()
                for i, student in enumerate(students, 1):
                    student.admission_number = f'ADM-{i:04d}'
                
                db.session.commit()
                print("Successfully added admission_number column and populated existing records.")
            else:
                print("admission_number column already exists.")
                
        except Exception as e:
            db.session.rollback()
            print(f"An error occurred: {str(e)}")
            raise

if __name__ == '__main__':
    add_admission_column()
