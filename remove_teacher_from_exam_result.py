from app import app, db
from sqlalchemy import text

def upgrade():
    with app.app_context():
        with db.engine.connect() as connection:
            # Disable foreign key constraints
            connection.execute(text('PRAGMA foreign_keys=off;'))
            connection.commit()
            
            # Create a new table without the teacher_id column
            connection.execute(text('''
            CREATE TABLE IF NOT EXISTS exam_result_new (
                id INTEGER NOT NULL, 
                student_id INTEGER NOT NULL, 
                exam_type VARCHAR(50) NOT NULL, 
                marks_obtained FLOAT NOT NULL, 
                total_marks FLOAT NOT NULL, 
                grade VARCHAR(2) NOT NULL, 
                remarks VARCHAR(200), 
                created_at DATETIME, 
                PRIMARY KEY (id), 
                FOREIGN KEY(student_id) REFERENCES student (id)
            )
            '''))
            connection.commit()
            
            # Copy data from the old table to the new table (excluding teacher_id)
            connection.execute(text('''
            INSERT INTO exam_result_new 
            (id, student_id, exam_type, marks_obtained, total_marks, grade, remarks, created_at)
            SELECT id, student_id, exam_type, marks_obtained, total_marks, grade, remarks, created_at
            FROM exam_result
            '''))
            connection.commit()
            
            # Drop the old table and rename the new one
            connection.execute(text('DROP TABLE IF EXISTS exam_result'))
            connection.execute(text('ALTER TABLE exam_result_new RENAME TO exam_result'))
            
            # Recreate indexes
            connection.execute(text('CREATE INDEX IF NOT EXISTS ix_exam_result_created_at ON exam_result (created_at)'))
            connection.execute(text('CREATE INDEX IF NOT EXISTS ix_exam_result_student_id ON exam_result (student_id)'))
            
            # Re-enable foreign key constraints
            connection.execute(text('PRAGMA foreign_key_check;'))
            connection.execute(text('PRAGMA foreign_keys=on;'))
            connection.commit()
        
        print("Successfully removed teacher_id from exam_result table")

if __name__ == '__main__':
    upgrade()
