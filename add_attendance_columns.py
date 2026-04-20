#!/usr/bin/env python3
"""
Migration script to add session_type and qr_token columns to attendance table.
Run: python add_attendance_columns.py
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import db, Attendance
from sqlalchemy import text
from app import app

def migrate():
    with app.app_context():
        # Check if columns exist
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('attendance')]
        
        if 'session_type' not in columns:
            print("Adding session_type column...")
            db.session.execute(text("ALTER TABLE attendance ADD COLUMN session_type VARCHAR(20) NOT NULL DEFAULT 'class'"))
            print("✓ session_type added")
        
        if 'qr_token' not in columns:
            print("Adding qr_token column...")
            db.session.execute(text("ALTER TABLE attendance ADD COLUMN qr_token VARCHAR(64) UNIQUE"))
            print("✓ qr_token added")
        
        # Update existing records
        existing = Attendance.query.all()
        import uuid
        for att in existing:
            att.session_type = 'class'  # Default for legacy data
            if not att.qr_token:
                att.qr_token = str(uuid.uuid4().hex)[:32]
        
        db.session.commit()
        print(f"✓ Migrated {len(existing)} existing records")
        print("Migration complete! Run 'python app.py' to test.")

if __name__ == '__main__':
    migrate()

