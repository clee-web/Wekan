import os
import random
import string
from flask import Flask, render_template, request, redirect, url_for, send_file, flash, session, abort
from flask_mail import Mail, Message
from datetime import datetime, timedelta, timezone
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from models import db, Student, Payment, ExamResult, Admin, Attendance, Expenditure
from sqlalchemy import or_, func, distinct, and_
from dotenv import load_dotenv
import pandas as pd
import io
import qrcode
from io import BytesIO
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
from auto_absent import auto_mark_absent


# Initialize Flask app and extensions
app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_routes.admin_login'
mail = Mail()
mail.init_app(app)

# Configure app
if os.getenv('SUPABASE_DB_URL'):
    DATABASE_URL = os.getenv('SUPABASE_DB_URL')
else:
    DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{os.path.join(os.path.dirname(__file__), "instance/academy.db")}')

app.config.update(
    SQLALCHEMY_DATABASE_URI=DATABASE_URL,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SECRET_KEY=os.getenv('SECRET_KEY', 'dev-secret-key'),
    SESSION_COOKIE_NAME='academy_session',
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_HTTPONLY=True,
    PERMANENT_SESSION_LIFETIME=timedelta(hours=24),
    MAIL_SERVER=os.getenv('MAIL_SERVER', 'smtp.gmail.com'),
    MAIL_PORT=int(os.getenv('MAIL_PORT', 465)),
    MAIL_USE_TLS=False,
    MAIL_USE_SSL=True,
    MAIL_USERNAME=os.getenv('MAIL_USERNAME', 'sokwayo@gmail.com'),
    MAIL_PASSWORD=os.getenv('MAIL_PASSWORD', 'dyom ajrl dadb wvih'),
    MAIL_DEFAULT_SENDER=os.getenv('MAIL_DEFAULT_SENDER', 'sokwayo@gmail.com')
)

db.init_app(app)
migrate = Migrate(app, db)
app.mail = mail

# Custom Jinja filters
@app.template_filter('datetimeformat')
def datetimeformat_filter(value, format='%Y-%m-%d %H:%M:%S'):
    if value == 'now':
        return datetime.now().strftime(format)
    elif isinstance(value, datetime):
        return value.strftime(format)
    else:
        return str(value)

@app.template_filter('format_number')
def format_number_filter(value):
    if value is None:
        return '0'
    try:
        return f"{float(value):,.2f}"
    except (ValueError, TypeError):
        return str(value)

from routes.admin_routes import admin_routes
app.register_blueprint(admin_routes)

@login_manager.user_loader
def load_user(user_id):
    from flask import session
    user_type = session.get('user_type')
    
    if user_type == 'SubAdmin':
        from models import SubAdmin
        return SubAdmin.query.get(user_id)
    elif user_type == 'TeacherLogin':
        from models import TeacherLogin
        return TeacherLogin.query.get(user_id)
    else:
        from models import Admin
        admin = Admin.query.get(user_id)
        if admin:
            return admin
        from models import SubAdmin
        return SubAdmin.query.get(user_id) or None

from routes.mpesa_routes import mpesa_bp
from routes.main import main_routes
from routes.test_routes import test_routes
from routes.qr_routes import qr_routes
from routes.teacher_routes import teacher_routes
from routes.supabase_routes import supabase_bp

app.register_blueprint(mpesa_bp, url_prefix='/mpesa')
app.register_blueprint(main_routes, url_prefix='/main')
app.register_blueprint(test_routes, url_prefix='/test')
app.register_blueprint(qr_routes)
app.register_blueprint(teacher_routes)
app.register_blueprint(supabase_bp, url_prefix='/api/supabase')

# Root route - redirect to dashboard
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    if path == '':
        if current_user.is_authenticated:
            return redirect(url_for('main.index'))
        else:
            return redirect(url_for('login'))
    
    # Custom 404 handler
    return render_template('404.html'), 404

load_dotenv()

@app.context_processor
def inject_now():
    graduation_count = db.session.query(func.count(distinct(Payment.student_id))).\
            join(Student).\
            filter(Student.active == True).\
            filter(Payment.payment_type == 'Graduation Fee').scalar() or 0
    return {'now': datetime.now(timezone.utc), 'graduation_count': graduation_count}

@app.route('/api/class-stats', methods=['GET'])
@login_required
def get_class_stats():
    try:
        class_distribution = db.session.query(
            Student.class_name,
            func.count(Student.id).label('student_count')
        ).group_by(Student.class_name).all()
        payment_status = db.session.query(
            Student.class_name,
            func.count(Payment.id).filter(Payment.status == 'cleared').label('full_payments'),
            func.count(Payment.id).filter(Payment.status == 'pending').label('partial_payments'),
            func.count(Student.id).filter(~Payment.status.in_(['cleared', 'pending'])).label('no_payments')
        ).outerjoin(Payment, Student.id == Payment.student_id).group_by(Student.class_name).all()
        
        classes = [item[0] for item in class_distribution]
        return {
            'classes': classes,
            'studentCounts': [item[1] for item in class_distribution],
            'fullPayments': [item[1] for item in payment_status],
            'partialPayments': [item[2] for item in payment_status],
            'noPayments': [item[3] for item in payment_status]
        }
    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'admin' and password in ['admin123', 'adminiyf']:
            from models import Admin
            admin = Admin.query.filter_by(username='admin').first() or Admin(username='admin')
            admin.set_password('adminiyf')
            db.session.add(admin)
            db.session.commit()
            if admin.check_password(password):
                login_user(admin)
                flash('Logged in successfully!', 'success')
                return redirect(url_for('main.index'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out!', 'success')
    return redirect(url_for('login'))

# Financial Report with PDF support
@app.route('/financial_report', methods=['GET'])
@login_required
def financial_report():
    selected_session = request.args.get('session', 'all')
    selected_year = request.args.get('year', 'all')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    sessions = db.session.query(Student.session).distinct().all()
    
    payment_query = db.session.query(
        Payment.payment_type,
        Student.session.label('session'),
        Payment.status,
        func.count(Payment.id).label('count'),
        func.sum(Payment.amount).label('total_amount')
    ).join(Student)
    
    if selected_session != 'all':
        payment_query = payment_query.filter(Student.session == selected_session)
    if selected_year != 'all':
        payment_query = payment_query.filter(func.strftime('%Y', Payment.date) == selected_year)
    if date_from:
        payment_query = payment_query.filter(Payment.date >= datetime.strptime(date_from, '%Y-%m-%d'))
    if date_to:
        payment_query = payment_query.filter(Payment.date <= datetime.strptime(date_to, '%Y-%m-%d'))

    payment_stats = payment_query.group_by(Payment.payment_type, Student.session, Payment.status).all()
    total_revenue = sum(stat.total_amount for stat in payment_stats)
    
    # Monthly trends
    payment_trends = db.session.query(
        func.strftime('%Y-%m', Payment.date).label('month'),
        func.sum(Payment.amount).label('total_amount')
    ).filter(Payment.date >= datetime.now() - timedelta(days=365)).group_by(func.strftime('%Y-%m', Payment.date)).order_by(func.strftime('%Y-%m', Payment.date)).all()

    cash_trends = db.session.query(
        func.strftime('%Y-%m', Payment.date).label('month'),
        func.sum(Payment.amount).label('cash')
    ).filter(Payment.payment_method == 'cash', Payment.date >= datetime.now() - timedelta(days=365)).group_by(func.strftime('%Y-%m', Payment.date)).all()
    
    mpesa_trends = db.session.query(
        func.strftime('%Y-%m', Payment.date).label('month'),
        func.sum(Payment.amount).label('mpesa')
    ).filter(Payment.payment_method == 'mpesa', Payment.date >= datetime.now() - timedelta(days=365)).group_by(func.strftime('%Y-%m', Payment.date)).all()
    
    expenditure_trends = db.session.query(
        func.strftime('%Y-%m', Expenditure.date).label('month'),
        func.sum(Expenditure.amount).label('expenditure')
    ).filter(Expenditure.date >= datetime.now() - timedelta(days=365)).group_by(func.strftime('%Y-%m', Expenditure.date)).order_by(func.strftime('%Y-%m', Expenditure.date)).all()
    
    # Merge data
    monthly_dict = {}
    for trend in payment_trends:
        month = trend.month
        monthly_dict[month] = {'month': month.replace('-', '/'), 'revenue': trend.total_amount or 0, 'cash': 0, 'mpesa': 0, 'expenditure': 0}
    
    for cash in cash_trends:
        if cash.month in monthly_dict:
            monthly_dict[cash.month]['cash'] = cash.cash or 0
    
    for mpesa in mpesa_trends:
        if mpesa.month in monthly_dict:
            monthly_dict[mpesa.month]['mpesa'] = mpesa.mpesa or 0
    
    for exp in expenditure_trends:
        if exp.month in monthly_dict:
            monthly_dict[exp.month]['expenditure'] = exp.expenditure or 0
    
    monthly_data = []
    for data in monthly_dict.values():
        data['net'] = data['revenue'] - data['expenditure']
        monthly_data.append(data)
    
    total_cash = sum(d['cash'] for d in monthly_data)
    total_mpesa = sum(d['mpesa'] for d in monthly_data)
    total_revenue = sum(d['revenue'] for d in monthly_data)
    total_expenditure = sum(d['expenditure'] for d in monthly_data)
    net_profit = total_revenue - total_expenditure
    
    recent_payments = Payment.query.order_by(Payment.date.desc()).limit(10).all()
    
    return render_template('financial_report.html',
                         payment_stats=payment_stats,
                         total_revenue=total_revenue,
                         payment_trends=payment_trends,
                         recent_payments=recent_payments,
                         monthly_data=monthly_data,
                         total_cash=total_cash,
                         total_mpesa=total_mpesa,
                         total_expenditure=total_expenditure,
                         net_profit=net_profit,
                         sessions=sessions)

@app.route('/financial_print')
@login_required
def financial_print():
    print_date = datetime.now().strftime('%d %B %Y')
    
    payment_trends = db.session.query(
        func.strftime('%Y-%m', Payment.date).label('month'),
        func.sum(Payment.amount).label('total_amount')
    ).group_by(func.strftime('%Y-%m', Payment.date)).order_by(func.strftime('%Y-%m', Payment.date)).all()

    cash_trends = db.session.query(
        func.strftime('%Y-%m', Payment.date).label('month'),
        func.sum(Payment.amount).label('cash')
    ).filter(Payment.payment_method == 'cash').group_by(func.strftime('%Y-%m', Payment.date)).all()
    
    mpesa_trends = db.session.query(
        func.strftime('%Y-%m', Payment.date).label('month'),
        func.sum(Payment.amount).label('mpesa')
    ).filter(Payment.payment_method == 'mpesa').group_by(func.strftime('%Y-%m', Payment.date)).all()
    
    expenditure_trends = db.session.query(
        func.strftime('%Y-%m', Expenditure.date).label('month'),
        func.sum(Expenditure.amount).label('expenditure')
    ).group_by(func.strftime('%Y-%m', Expenditure.date)).order_by(func.strftime('%Y-%m', Expenditure.date)).all()
    
    monthly_dict = {}
    for trend in payment_trends:
        month = trend.month
        monthly_dict[month] = {'month': month.replace('-', '/'), 'revenue': trend.total_amount or 0, 'cash': 0, 'mpesa': 0, 'expenditure': 0, 'net': 0}
    
    for cash in cash_trends:
        if cash.month in monthly_dict:
            monthly_dict[cash.month]['cash'] = cash.cash or 0
    
    for mpesa in mpesa_trends:
        if mpesa.month in monthly_dict:
            monthly_dict[mpesa.month]['mpesa'] = mpesa.mpesa or 0
    
    for exp in expenditure_trends:
        if exp.month in monthly_dict:
            monthly_dict[exp.month]['expenditure'] = exp.expenditure or 0
    
    monthly_data = []
    for data in monthly_dict.values():
        data['net'] = data['revenue'] - data['expenditure']
        monthly_data.append(data)
    
    total_cash = sum(d['cash'] for d in monthly_data)
    total_mpesa = sum(d['mpesa'] for d in monthly_data)
    total_revenue = sum(d['revenue'] for d in monthly_data)
    total_expenditure = sum(d['expenditure'] for d in monthly_data)
    net_profit = total_revenue - total_expenditure
    
    start_date = monthly_data[0]['month'] if monthly_data else 'N/A'
    end_date = monthly_data[-1]['month'] if monthly_data else 'N/A'
    
    return render_template('financial_print.html',
                          monthly_data=monthly_data,
                          total_cash=total_cash,
                          total_mpesa=total_mpesa,
                          total_revenue=total_revenue,
                          total_expenditure=total_expenditure,
                          net_profit=net_profit,
                          start_date=start_date,
                          end_date=end_date,
                          print_date=print_date)

# Other routes...
# ... (rest of app.py routes remain the same)

