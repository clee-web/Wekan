import os
import random
import string
from flask import Flask, render_template, request, redirect, url_for, send_file, flash, session
from datetime import datetime, timedelta, timezone
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from models import db, Student, Payment, ExamResult, Admin
from sqlalchemy import or_, func, distinct
from dotenv import load_dotenv
import pandas as pd
import io
import qrcode
from io import BytesIO
from flask import send_file

# Initialize Flask app and extensions
app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_routes.admin_login'

# Configure app
app.config.update(
    SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL', f'sqlite:///{os.path.join(os.path.dirname(__file__), "instance/academy.db")}'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SECRET_KEY=os.getenv('SECRET_KEY', 'dev-secret-key'),
    SESSION_COOKIE_NAME='academy_session',
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_HTTPONLY=True,
    PERMANENT_SESSION_LIFETIME=timedelta(hours=24)
)

# Initialize database
db.init_app(app)
migrate = Migrate(app, db)

# Register blueprints AFTER all imports
from routes import admin_routes, main_routes, mpesa_routes, test_routes, qr_routes, teacher_routes
app.register_blueprint(admin_routes)
app.register_blueprint(mpesa_routes, url_prefix='/mpesa')
app.register_blueprint(main_routes)
app.register_blueprint(test_routes, url_prefix='/test')
app.register_blueprint(qr_routes)
app.register_blueprint(teacher_routes, url_prefix='/teacher')  # ADD THIS LINE

# User loader
@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(user_id)

load_dotenv()

@app.context_processor
def inject_now():
    graduation_count = db.session.query(func.count(distinct(Payment.student_id))).join(Student).filter(Student.active == True).filter(Payment.payment_type == 'Graduation Fee').scalar() or 0
    return {'now': datetime.now(timezone.utc), 'graduation_count': graduation_count}

# [rest of routes unchanged... copy the rest from app.py]

# Copy the remaining routes from your current app.py here...
# ... (all @app.route routes remain the same)

if __name__ == '__main__':
    with app.app_context():
        os.makedirs('instance', exist_ok=True)
        db_path = os.path.join('instance', 'academy.db')
        if not os.path.exists(db_path):
            db.create_all()
            print(f"Database created at {db_path}")
        else:
            print(f"Using existing database at {db_path}")
            db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)
