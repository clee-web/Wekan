#!/usr/bin/env python3
"""
Clean Flask app launcher for IYF Academy - Fixed version
"""
import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from app import app, db
    # Avoid UnicodeEncodeError on Windows consoles with non-UTF8 code pages.
    print("[OK] IYF Academy app loaded successfully!")
    print("[START] Server: http://127.0.0.1:5000")
    print("[LOGIN] admin / adminiyf")
    
    # Create tables only if database is empty (migration preferred)
    with app.app_context():
        inspector = db.inspect(db.engine)
        if not inspector.has_table('teacher_login'):
            db.create_all()
            print("[OK] Database tables created (fresh DB)")
        else:
            print("[OK] Database exists - migrations should be used for schema changes")

    
    app.run(host='0.0.0.0', port=5000, debug=True)
    
except ImportError as e:
    print(f"[ERROR] Import error: {e}")
    print("Install requirements:")
    print("pip install flask flask-sqlalchemy flask-login flask-mail flask-migrate pandas python-dotenv qrcode[pil] apscheduler")
    
except Exception as e:
    print(f"[ERROR] Error: {e}")
    print("Check app.py syntax and dependencies")

