import sqlite3
from app import app
from models import db, Student

with app.app_context():
    # Connect directly to SQLite DB to add column
    db_path = db.engine.url.database  # instance/academy.db
    conn = sqlite3.connect(db_path)
    
    cursor = conn.cursor()
    try:
        cursor.execute('ALTER TABLE student ADD COLUMN next_of_kin VARCHAR(100)')
        conn.commit()
        print("✓ Added next_of_kin column to student table")
    except sqlite3.OperationalError as e:
        if 'duplicate column name' in str(e):
            print("✓ next_of_kin column already exists")
        else:
            print(f"✗ Error adding column: {e}")
    
    # Update existing students
    cursor.execute("UPDATE student SET next_of_kin = '' WHERE next_of_kin IS NULL OR next_of_kin = ''")
    updated = cursor.rowcount
    conn.commit()
    print(f"✓ Updated {updated} students with empty next_of_kin")
    
    conn.close()
    
    print("\nRun 'flask db stamp head' if using migrations, then restart app")

