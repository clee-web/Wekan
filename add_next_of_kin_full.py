import sqlite3
from app import app
from models import db, Student

with app.app_context():
    db_path = db.engine.url.database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Add 3 columns
    columns = [
        'next_of_kin_name VARCHAR(100)',
        'next_of_kin_relationship VARCHAR(50)',
        'next_of_kin_phone VARCHAR(20)'
    ]
    
    for col in columns:
        try:
            cursor.execute(f'ALTER TABLE student ADD COLUMN {col}')
            print(f"✓ Added {col}")
        except sqlite3.OperationalError as e:
            if 'duplicate column name' in str(e):
                print(f"✓ {col} already exists")
            else:
                print(f"✗ Error {col}: {e}")
    
    # Update existing with empty values
    cursor.execute("UPDATE student SET next_of_kin_name = '', next_of_kin_relationship = '', next_of_kin_phone = '' WHERE next_of_kin_name IS NULL")
    updated = cursor.rowcount
    conn.commit()
    print(f"✓ Updated {updated} students")
    
    conn.close()
    print("DB ready. Restart app to test.")
