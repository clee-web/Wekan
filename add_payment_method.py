from flask import Flask
from models import db, Payment
import os
from sqlalchemy import text
import sqlite3

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/academy.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def add_payment_method_column():
    # Connect directly to SQLite database
    conn = sqlite3.connect('instance/academy.db')
    cursor = conn.cursor()
    
    try:
        # Drop payment_new table if it exists (from previous failed attempts)
        cursor.execute('DROP TABLE IF EXISTS payment_new')
        
        # Create new table with all required columns
        cursor.execute('''
            CREATE TABLE payment_new (
                id INTEGER NOT NULL PRIMARY KEY,
                student_id INTEGER NOT NULL,
                transaction_number VARCHAR(20) NOT NULL UNIQUE,
                amount FLOAT NOT NULL,
                payment_type VARCHAR(50) NOT NULL,
                payment_method VARCHAR(10) NOT NULL DEFAULT 'cash',
                date DATETIME,
                status VARCHAR(20) NOT NULL DEFAULT 'completed',
                payment_category VARCHAR(50) NOT NULL DEFAULT 'regular',
                year VARCHAR(4) NOT NULL DEFAULT '2024',
                session VARCHAR(20) NOT NULL DEFAULT 'Term 1',
                notes TEXT,
                last_modified DATETIME,
                FOREIGN KEY(student_id) REFERENCES student(id)
            )
        ''')
        
        # Copy existing data with default values for new columns
        cursor.execute('''
            INSERT INTO payment_new (
                id,
                student_id,
                transaction_number,
                amount,
                payment_type,
                date,
                payment_method,
                status,
                payment_category,
                year,
                session,
                notes,
                last_modified
            )
            SELECT 
                id,
                student_id,
                transaction_number,
                amount,
                payment_type,
                date,
                'cash',
                'completed',
                'regular',
                '2024',
                'Term 1',
                NULL,
                date
            FROM payment
        ''')
        
        # Drop old table
        cursor.execute('DROP TABLE payment')
        
        # Rename new table
        cursor.execute('ALTER TABLE payment_new RENAME TO payment')
        
        # Commit changes
        conn.commit()
        print("Successfully updated payment table schema")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    add_payment_method_column()
