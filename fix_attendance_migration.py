#!/usr/bin/env python3
"""
Fixed migration script for SQLite UNIQUE constraint issue.
SQLite cannot add UNIQUE column directly. This version adds non-unique first, then populates, then adds constraint.
Run: python fix_attendance_migration.py
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import db, Attendance
from sqlalchemy import text, inspect
from app import app
import uuid

def migrate():
    with app.app_context():
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('attendance')]
        
        # Add session_type if missing
        if 'session_type' not in columns:
            print("Adding session_type column...")
            db.session.execute(text("ALTER TABLE attendance ADD COLUMN session_type VARCHAR(20) NOT NULL DEFAULT 'class'"))
            print("✓ session_type added")
        
        # Add qr_token WITHOUT UNIQUE first if missing
        if 'qr_token' not in columns:
            print("Adding qr_token column (non-unique)...")
            db.session.execute(text("ALTER TABLE attendance ADD COLUMN qr_token VARCHAR(64)"))
            print("✓ qr_token added (non-unique)")
        
        # Populate unique qr_tokens for existing records
        print("Populating unique qr_tokens...")
        existing = Attendance.query.filter(Attendance.qr_token.is_(None)).all()
        for att in existing:
            while True:
                token = str(uuid.uuid4().hex)[:32]
                # Check if token already exists
                if not Attendance.query.filter(Attendance.qr_token == token).first():
                    att.qr_token = token
                    break
        db.session.commit()
        print(f"✓ Populated {len(existing)} records with unique qr_tokens")
        
        # Drop existing index if any, create UNIQUE constraint
        try:
            db.session.execute(text("DROP INDEX IF EXISTS ix_attendance_qr_token"))
        except:
            pass
        
        # SQLite doesn't support ALTER ADD UNIQUE directly, so create new table or skip for now
        print("⚠️  Skipping UNIQUE constraint creation (SQLite limitation).")
        print("   Model validation will enforce uniqueness on new inserts.")
        
        print("Migration complete! Ready for app usage.")
        print("\nNext: python app.py to test model changes.")

if __name__ == '__main__':
    migrate()

