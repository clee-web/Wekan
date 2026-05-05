#!/usr/bin/env python3
from app import app
from models import db, TeacherLogin
from datetime import datetime

with app.app_context():
    import sys
    if len(sys.argv) > 1:
        username = sys.argv[1]
    else:
        username = input("Enter teacher username (email): ").strip()
    
    login = TeacherLogin.query.filter_by(username=username).first()
    if login:
        print(f"Found {login.username}, teacher: {login.teacher.name if login.teacher else 'No teacher'}")
        print(f"Old hash: {login.password_hash[:50]}...")
        print(f"Old admin_set_timestamp: {login.admin_set_timestamp}")
        print(f"Old needs_reset: {login.needs_password_reset()}")
        
        new_password = input(f"Enter new password for {username} (or press Enter for 'teacher123'): ").strip()
        if not new_password:
            new_password = 'teacher123'
        
        login.set_password(new_password, admin_set=True)
        db.session.commit()
        
        print("✅ Password reset!")
        print(f"Username: {login.username}")
        print(f"Password: {new_password}")
        print(f"New hash: {login.password_hash[:50]}...")
        print(f"admin_set_timestamp: {login.admin_set_timestamp}")
        print(f"needs_password_reset(): {login.needs_password_reset()}")
    else:
        print(f"❌ No TeacherLogin found for '{username}'")
        print("Available teachers:")
        for tl in TeacherLogin.query.all():
            print(f"  - {tl.username} ({tl.teacher.name if tl.teacher else 'No teacher'})")

