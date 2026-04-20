import os
import random
import string
from flask import Flask, render_template, request, redirect, url_for, send_file, flash, session
from flask_mail import Mail, Message
from datetime import datetime, timedelta, timezone
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from models import db, Student, Payment, ExamResult, Admin, Attendance
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
mail = Mail()
mail.init_app(app)

# Configure app
app.config.update(
    SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL', f'sqlite:///{os.path.join(os.path.dirname(__file__), "instance/academy.db")}'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SECRET_KEY=os.getenv('SECRET_KEY', 'dev-secret-key'),  # Use a more secure default
    SESSION_COOKIE_NAME='academy_session',
    SESSION_COOKIE_SECURE=False,  # Allow session cookies over HTTP for local development
    SESSION_COOKIE_HTTPONLY=True,
    PERMANENT_SESSION_LIFETIME=timedelta(hours=24),
    # Email configuration
    MAIL_SERVER=os.getenv('MAIL_SERVER', 'smtp.gmail.com'),
    MAIL_PORT=int(os.getenv('MAIL_PORT', 465)),
    MAIL_USE_TLS=False,
    MAIL_USE_SSL=True,
    MAIL_USERNAME=os.getenv('MAIL_USERNAME', 'sokwayo@gmail.com'),
    MAIL_PASSWORD=os.getenv('MAIL_PASSWORD', 'dyom ajrl dadb wvih'),
    MAIL_DEFAULT_SENDER=os.getenv('MAIL_DEFAULT_SENDER', 'sokwayo@gmail.com')
)

# Initialize database
db.init_app(app)
migrate = Migrate(app, db)

# Attach mail to app for access in routes
app.mail = mail

# Add custom Jinja filters
from datetime import datetime

@app.template_filter('datetimeformat')
def datetimeformat_filter(value, format='%Y-%m-%d %H:%M:%S'):
    if value == 'now':
        return datetime.now().strftime(format)
    elif isinstance(value, datetime):
        return value.strftime(format)
    else:
        return str(value)

from routes.admin_routes import admin_routes
app.register_blueprint(admin_routes)

# User loader for both admin and teacher login
from flask_login import UserMixin
from models import Admin, TeacherLogin

@login_manager.user_loader
def load_user(user_id):
    # Try to load as Admin first
    admin = Admin.query.get(user_id)
    if admin:
        return admin
    
    # Try to load as TeacherLogin
    teacher_login = TeacherLogin.query.get(user_id)
    if teacher_login:
        return teacher_login
    
    return None

# Register blueprints
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

# Load environment variables
load_dotenv()

# Context processor for template variables
@app.context_processor
def inject_now():
    graduation_count = db.session.query(func.count(distinct(Payment.student_id))).\
            join(Student).\
            filter(Student.active == True).\
            filter(Payment.payment_type == 'Graduation Fee').scalar() or 0
    return {'now': datetime.now(timezone.utc), 'graduation_count': graduation_count}

# API endpoint for class statistics
@app.route('/api/class-stats', methods=['GET'])
@login_required
def get_class_stats():
    try:
        # Get class distribution
        class_distribution = db.session.query(
            Student.class_name,
            func.count(Student.id).label('student_count')
        ).group_by(Student.class_name).all()

        # Get payment status by class
        payment_status = db.session.query(
            Student.class_name,
            func.count(Payment.id).filter(Payment.status == 'cleared').label('full_payments'),
            func.count(Payment.id).filter(Payment.status == 'pending').label('partial_payments'),
            func.count(Student.id).filter(~Payment.status.in_(['cleared', 'pending'])).label('no_payments')
        ).outerjoin(Payment, Student.id == Payment.student_id).group_by(Student.class_name).all()

        # Convert results to dictionaries
        classes = [item[0] for item in class_distribution]
        student_counts = [item[1] for item in class_distribution]
        full_payments = [item[1] for item in payment_status]
        partial_payments = [item[2] for item in payment_status]
        no_payments = [item[3] for item in payment_status]

        return {
            'classes': classes,
            'studentCounts': student_counts,
            'fullPayments': full_payments,
            'partialPayments': partial_payments,
            'noPayments': no_payments
        }
    except Exception as e:
        return {'error': str(e)}, 500

# Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            password = request.form.get('password')
            
            if not username or not password:
                flash('Username and password are required', 'danger')
                return render_template('login.html')

            # Handle hardcoded admin login (supports both admin123 and adminiyf)
            if username == 'admin' and password in ['admin123', 'adminiyf']:
                from models import Admin
                admin = Admin.query.filter_by(username='admin').first()
                if not admin:
                    # Create admin if doesn't exist
                    admin = Admin(username='admin')
                    admin.set_password('admin123')  # Default password
                    db.session.add(admin)
                    db.session.commit()

                    # Auto-sync to Supabase
                    try:
                        from supabase_sync import sync_admin_to_supabase
                        sync_admin_to_supabase(admin)
                    except Exception as e:
                        print(f"Supabase sync error: {str(e)}")
                if admin.check_password(password):
                    login_user(admin)
                    flash('Logged in successfully!', 'success')
                    next_page = request.args.get('next', url_for('main.index'))
                    return redirect(next_page)
                else:
                    flash('Invalid password for admin', 'danger')
                    return render_template('login.html')
            else:
                flash('Invalid username or password', 'danger')
                return render_template('login.html')
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')
            app.logger.error(f'Login error: {str(e)}')
            return render_template('login.html')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return redirect(url_for('main.index'))

@app.route('/add_student', methods=['GET', 'POST'])
@login_required
def add_student():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        residence = request.form['residence']
        class_name = request.form['class']
        session = request.form['session']

        new_student = Student(name=name, phone=phone, residence=residence, class_name=class_name, session=session)
        db.session.add(new_student)
        db.session.commit()
        flash('Student added successfully. Please make the initial payment.', 'success')
        return redirect(url_for('manage_payments', student_id=new_student.id))
    return render_template('add_student.html')

def generate_transaction_number():
    """Generate a unique transaction number"""
    prefix = 'TRX'
    random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"{prefix}{random_chars}"

@app.route('/manage_payments/<int:student_id>', methods=['GET', 'POST'])
@login_required
def manage_payments(student_id):
    student = Student.query.get_or_404(student_id)
    
    if request.method == 'POST':
        payment_method = request.form.get('payment_method')
        payment_type = request.form.get('payment_type')
        amount = request.form.get('amount')
        transaction_number = request.form.get('transaction_number')
        
        # Generate transaction number if not M-PESA
        if payment_method != 'mpesa':
            transaction_number = generate_transaction_number()
        
        try:
            current_time = datetime.now()
            new_payment = Payment(
                student_id=student_id,
                payment_method=payment_method,
                payment_type=payment_type,
                amount=float(amount),
                transaction_number=transaction_number,
                date=current_time,
                year=current_time.year,
                session=student.session
            )
            
            # Add the new payment
            db.session.add(new_payment)
            db.session.flush()
            
            # Calculate total paid for this student
            total_paid = db.session.query(db.func.sum(Payment.amount)).\
                filter(Payment.student_id == student_id).scalar() or 0
                
            # Update the status of all payments
            new_payment.update_status()
            
            # Commit all changes
            db.session.commit()
            
            # Show appropriate message
            if total_paid >= 1500.0:
                flash('Payment recorded successfully! All fees cleared.', 'success')
            else:
                remaining = 1500.0 - total_paid
                flash(f'Payment recorded successfully! Remaining balance: KES {remaining:.2f}', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error recording payment: {str(e)}', 'error')
    
    payments = Payment.query.filter_by(student_id=student_id).all()
    return render_template('manage_payments.html', student=student, payments=payments)

@app.route('/receipt/<int:payment_id>')
@login_required
def view_receipt(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    student = Student.query.get_or_404(payment.student_id)
    return render_template('receipt.html', payment=payment, student=student)

@app.route('/delete_payment/<int:payment_id>', methods=['POST'])
@login_required
def delete_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    db.session.delete(payment)
    db.session.commit()
    flash('Payment deleted successfully', 'success')
    return redirect(url_for('manage_payments', student_id=payment.student_id))

@app.route('/remove_duplicates/<int:student_id>', methods=['POST'])
@login_required
def remove_duplicates(student_id):
    """Remove duplicate payments for specific student."""
    removed = Payment.remove_duplicates(student_id=student_id, dry_run=False)
    if removed > 0:
        flash(f'Removed {removed} duplicate payments for this student!', 'success')
    else:
        flash('No duplicates found for this student.', 'info')
    return redirect(url_for('manage_payments', student_id=student_id))

@app.route('/delete_student/<int:student_id>', methods=['POST'])
@login_required
def delete_student(student_id):
    try:
        student = Student.query.get_or_404(student_id)
        
        # Delete related exam results
        ExamResult.query.filter_by(student_id=student_id).delete(synchronize_session=False)
        
        # Delete related payments
        Payment.query.filter_by(student_id=student_id).delete(synchronize_session=False)
        
        # Delete the student
        db.session.delete(student)
        db.session.commit()
        
        flash('Student and all related data have been deleted successfully', 'success')
        return redirect(url_for('search_students'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting student: {str(e)}', 'error')
        return redirect(url_for('view_student', student_id=student_id))

@app.route('/download_report')
@login_required
def download_report():
    # Get filter parameters (same as report route)
    selected_session = request.args.get('session', 'all')
    selected_year = request.args.get('academic_year', 'all')
    selected_semester = request.args.get('semester', 'all')
    selected_category = request.args.get('payment_category', 'all')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    # Query payments with student information
    query = db.session.query(
        Student.name.label('Student Name'),
        Student.class_name.label('Class'),
        Student.session.label('Session'),
        Payment.transaction_number.label('Transaction Number'),
        Payment.amount.label('Amount'),
        Payment.payment_type.label('Payment Type'),
        Payment.payment_method.label('Payment Method'),
        Payment.status.label('Status'),
        Payment.date.label('Date'),
        Payment.notes.label('Notes')
    ).join(Student)
    
    # Apply filters
    if selected_session != 'all':
        query = query.filter(Student.session == selected_session)
    if selected_year != 'all':
        query = query.filter(Student.session == selected_year)
    if selected_semester != 'all':
        query = query.filter(Student.session == selected_semester)
    if selected_category != 'all':
        query = query.filter(Payment.payment_type == selected_category)
    if date_from:
        query = query.filter(Payment.date >= datetime.strptime(date_from, '%Y-%m-%d'))
    if date_to:
        query = query.filter(Payment.date <= datetime.strptime(date_to, '%Y-%m-%d'))
    
    # Get the data
    payments = query.all()
    
    # Create DataFrame
    df = pd.DataFrame([payment._asdict() for payment in payments])
    
    # Create Excel file
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Write main payment data
        df.to_excel(writer, index=False, sheet_name='Payments')
        
        # Add summary sheet
        summary_data = {
            'Total Revenue': [df['Amount'].sum()],
            'Total Transactions': [len(df)],
            'Unique Students': [df['Student Name'].nunique()],
            'Date Range': [f"{df['Date'].min()} to {df['Date'].max()}"]
        }
        pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary')
        
        # Add payment type breakdown
        pivot_type = df.pivot_table(
            values='Amount',
            index='Payment Type',
            aggfunc=['count', 'sum']
        ).reset_index()
        pivot_type.to_excel(writer, sheet_name='Payment Type Breakdown')
        
        # Format the Excel file
        workbook = writer.book
        money_format = workbook.add_format({'num_format': '#,##0.00'})
        date_format = workbook.add_format({'num_format': 'yyyy-mm-dd'})
        
        for worksheet in writer.sheets.values():
            worksheet.set_column('A:Z', 15)
            
    output.seek(0)
    
    # Generate filename with filters
    filters = []
    if selected_session != 'all':
        filters.append(f"session_{selected_session}")
    if selected_year != 'all':
        filters.append(f"year_{selected_year}")
    if selected_semester != 'all':
        filters.append(f"sem_{selected_semester}")
    if selected_category != 'all':
        filters.append(f"cat_{selected_category}")
    
    filename = f"financial_report_{'_'.join(filters) if filters else 'all'}.xlsx"
    
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@app.route('/financial_report', methods=['GET'])
@login_required
def financial_report():
    # Get filter parameters
    selected_session = request.args.get('session', 'all')
    selected_year = request.args.get('year', 'all')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    # Get all available options for filters
    sessions = db.session.query(Student.session).distinct().all()
    years_query = db.session.query(func.strftime('%Y', Payment.date).label('year')).distinct()
    years = [(str(year[0]),) if year[0] else ('2024',) for year in years_query.all()]
    if not years:
        current_year = datetime.now().year
        years = [(str(year),) for year in range(current_year-5, current_year+6)]
    else:
        min_year = min(int(year[0]) for year in years)
        max_year = max(int(year[0]) for year in years)
        extended_years = set(str(year) for year in range(min_year-5, max_year+6))
        years = [(year,) for year in sorted(extended_years)]
    
    # Base query for payments
    payment_query = db.session.query(
        Payment.payment_type,
        Student.session.label('year'),
        Student.session.label('session'),
        Payment.status,
        func.count(Payment.id).label('count'),
        func.sum(Payment.amount).label('total_amount')
    ).join(Student)

    # Base query for exam results
    exam_query = db.session.query(
        Student.name,
        Student.class_name,
        Student.session,
        ExamResult.exam_type,
        ExamResult.marks_obtained,
        ExamResult.total_marks,
        ExamResult.grade,
        ExamResult.created_at
    ).join(Student)

    # Apply filters
    if selected_session != 'all':
        payment_query = payment_query.filter(Student.session == selected_session)
        exam_query = exam_query.filter(Student.session == selected_session)
    if selected_year != 'all':
        payment_query = payment_query.filter(func.strftime('%Y', Payment.date) == selected_year)
        exam_query = exam_query.filter(func.strftime('%Y', ExamResult.created_at) == selected_year)
    if date_from:
        date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
        payment_query = payment_query.filter(Payment.date >= date_from_obj)
        exam_query = exam_query.filter(ExamResult.created_at >= date_from_obj)
    if date_to:
        date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
        payment_query = payment_query.filter(Payment.date <= date_to_obj)
        exam_query = exam_query.filter(ExamResult.created_at <= date_to_obj)

    # Get payment statistics
    payment_stats = payment_query.group_by(
        Payment.payment_type,
        Student.session,
        Payment.status
    ).all()

    # Calculate summary statistics
    total_revenue = sum(stat.total_amount for stat in payment_stats)
    payment_methods = db.session.query(
        Payment.payment_method,
        func.count(Payment.id).label('count'),
        func.sum(Payment.amount).label('total_amount')
    ).group_by(Payment.payment_method).all()

    # Get payment trends (monthly)
    payment_trends = db.session.query(
        Payment.date.label('month'),  # Use the full date instead of strftime
        func.sum(Payment.amount).label('total_amount')
    ).group_by(func.strftime('%Y-%m', Payment.date)).order_by(func.strftime('%Y-%m', Payment.date)).all()

    # Get student payment status
    student_payments = db.session.query(
        Student.name,
        Student.class_name,
        func.sum(Payment.amount).label('total_paid')
    ).join(Payment).group_by(Student.id).all()

    # Get exam statistics
    exam_results = exam_query.all()
    
    # Calculate exam statistics
    exam_stats = db.session.query(
        ExamResult.exam_type,
        func.count(ExamResult.id).label('total_exams'),
        func.avg(ExamResult.marks_obtained * 100.0 / ExamResult.total_marks).label('avg_score'),
        func.min(ExamResult.marks_obtained * 100.0 / ExamResult.total_marks).label('min_score'),
        func.max(ExamResult.marks_obtained * 100.0 / ExamResult.total_marks).label('max_score')
    ).group_by(ExamResult.exam_type).all()

    # Calculate grade distribution
    grade_distribution = db.session.query(
        ExamResult.grade,
        func.count(ExamResult.id).label('count')
    ).group_by(ExamResult.grade).all()

    return render_template('financial_report.html',
                         payment_stats=payment_stats,
                         total_revenue=total_revenue,
                         payment_methods=payment_methods,
                         payment_trends=payment_trends,
                         student_payments=student_payments,
                         sessions=sessions,
                         years=years,
                         selected_session=selected_session,
                         selected_year=selected_year,
                         date_from=date_from,
                         date_to=date_to,
                         exam_results=exam_results,
                         exam_stats=exam_stats,
                         grade_distribution=grade_distribution)

@app.route('/download_financial_report')
@login_required
def download_financial_report():
    # Get filter parameters (same as report route)
    selected_session = request.args.get('session', 'all')
    selected_year = request.args.get('year', 'all')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    # Query payments with student information
    payment_query = db.session.query(
        Student.name.label('Student Name'),
        Student.class_name.label('Class'),
        Student.session.label('Session'),
        Payment.transaction_number.label('Transaction Number'),
        Payment.amount.label('Amount'),
        Payment.payment_type.label('Payment Type'),
        Payment.payment_method.label('Payment Method'),
        Payment.status.label('Status'),
        Payment.date.label('Date'),
        Payment.notes.label('Notes')
    ).join(Student)
    
    # Query exam results with student information
    exam_query = db.session.query(
        Student.name.label('Student Name'),
        Student.class_name.label('Class'),
        Student.session.label('Session'),
        ExamResult.exam_type.label('Exam Type'),
        ExamResult.marks_obtained.label('Marks Obtained'),
        ExamResult.total_marks.label('Total Marks'),
        ExamResult.grade.label('Grade'),
        ExamResult.remarks.label('Remarks'),
        ExamResult.created_at.label('Date')
    ).join(Student)
    
    # Apply filters
    if selected_session != 'all':
        payment_query = payment_query.filter(Student.session == selected_session)
        exam_query = exam_query.filter(Student.session == selected_session)
    if selected_year != 'all':
        payment_query = payment_query.filter(func.strftime('%Y', Payment.date) == selected_year)
        exam_query = exam_query.filter(func.strftime('%Y', ExamResult.created_at) == selected_year)
    if date_from:
        date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
        payment_query = payment_query.filter(Payment.date >= date_from_obj)
        exam_query = exam_query.filter(ExamResult.created_at >= date_from_obj)
    if date_to:
        date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
        payment_query = payment_query.filter(Payment.date <= date_to_obj)
        exam_query = exam_query.filter(ExamResult.created_at <= date_to_obj)
    
    # Get the data
    payments = payment_query.all()
    exam_results = exam_query.all()
    
    # Create DataFrames
    payments_df = pd.DataFrame([payment._asdict() for payment in payments])
    exams_df = pd.DataFrame([exam._asdict() for exam in exam_results])
    
    # Add percentage column to exams DataFrame
    if not exams_df.empty:
        exams_df['Percentage'] = (exams_df['Marks Obtained'] / exams_df['Total Marks'] * 100).round(2)
    
    # Create Excel file
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        
        # Format settings
        money_format = workbook.add_format({'num_format': '#,##0.00'})
        date_format = workbook.add_format({'num_format': 'yyyy-mm-dd'})
        percent_format = workbook.add_format({'num_format': '0.00%'})
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#f8f9fa',
            'border': 1
        })
        
        # Write payments data
        if not payments_df.empty:
            payments_df.to_excel(writer, index=False, sheet_name='Payments')
            worksheet = writer.sheets['Payments']
            worksheet.set_column('A:Z', 15)
            worksheet.set_row(0, None, header_format)
            
            # Format amount column
            amount_col = payments_df.columns.get_loc('Amount')
            worksheet.set_column(amount_col, amount_col, 15, money_format)
            
            # Format date column
            date_col = payments_df.columns.get_loc('Date')
            worksheet.set_column(date_col, date_col, 15, date_format)
        
        # Write exam results data
        if not exams_df.empty:
            # Calculate percentage for each exam
            exams_df['Percentage'] = (exams_df['Marks Obtained'] / exams_df['Total Marks'] * 100).round(2)
            
            # Create pivot table for exam results
            pivot_exams = pd.pivot_table(
                exams_df,
                values=['Marks Obtained', 'Total Marks', 'Grade', 'Percentage'],
                index=['Student Name', 'Class', 'Session'],
                columns=['Exam Type'],
                aggfunc={'Marks Obtained': 'first', 'Total Marks': 'first', 'Grade': 'first', 'Percentage': 'first'}
            )
            
            # Flatten column names
            pivot_exams.columns = [f"{exam_type} - {metric}" 
                                 for metric, exam_type in pivot_exams.columns]
            
            # Reset index to make Student Name, Class, and Session regular columns
            pivot_exams = pivot_exams.reset_index()
            
            # Calculate total percentage
            def calculate_total_percentage(row):
                percentages = [
                    row.get('Leadership Mid - Percentage', 0),
                    row.get('Class Mid - Percentage', 0),
                    row.get('Leadership Final - Percentage', 0),
                    row.get('Class Final - Percentage', 0)
                ]
                # Filter out None values
                percentages = [p for p in percentages if p is not None]
                if percentages:
                    return sum(percentages) / 2  # Divide by 2 as per requirement
                return 0
            
            # Add total percentage column
            pivot_exams['Total Percentage'] = pivot_exams.apply(calculate_total_percentage, axis=1).round(2)
            
            # Write to Excel
            pivot_exams.to_excel(writer, index=False, sheet_name='Exam Results')
            worksheet = writer.sheets['Exam Results']
            worksheet.set_column('A:Z', 15)
            worksheet.set_row(0, None, header_format)
            
            # Format percentage columns
            for col_idx, col_name in enumerate(pivot_exams.columns):
                if 'Percentage' in col_name:
                    worksheet.set_column(col_idx, col_idx, 15, percent_format)
                elif 'Grade' in col_name:
                    worksheet.set_column(col_idx, col_idx, 15)
        
        # Add summary sheet
        summary_data = {
            'Financial Summary': [
                'Total Revenue', payments_df['Amount'].sum() if not payments_df.empty else 0,
                'Total Transactions', len(payments_df) if not payments_df.empty else 0,
                'Unique Students (Payments)', payments_df['Student Name'].nunique() if not payments_df.empty else 0
            ],
            'Exam Summary': [
                'Total Exams', len(exams_df) if not exams_df.empty else 0,
                'Unique Students (Exams)', exams_df['Student Name'].nunique() if not exams_df.empty else 0,
                'Average Score', exams_df['Percentage'].mean() if not exams_df.empty else 0
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        # Add exam analysis sheet
        if not exams_df.empty:
            # Exam type breakdown
            exam_type_pivot = pd.pivot_table(
                exams_df,
                values=['Marks Obtained', 'Total Marks', 'Percentage'],
                index=['Exam Type'],
                aggfunc={
                    'Marks Obtained': ['count', 'mean'],
                    'Total Marks': 'mean',
                    'Percentage': ['mean', 'min', 'max']
                }
            ).round(2)
            
            # Grade distribution
            grade_dist = exams_df['Grade'].value_counts().reset_index()
            grade_dist.columns = ['Grade', 'Count']
            
            # Write to Excel
            exam_type_pivot.to_excel(writer, sheet_name='Exam Analysis')
            grade_dist.to_excel(writer, sheet_name='Grade Distribution', index=False)
            
            # Format sheets
            for sheet in ['Exam Analysis', 'Grade Distribution']:
                worksheet = writer.sheets[sheet]
                worksheet.set_column('A:Z', 15)
                worksheet.set_row(0, None, header_format)
    
    output.seek(0)
    
    # Generate filename with filters
    filters = []
    if selected_session != 'all':
        filters.append(f"session_{selected_session}")
    if selected_year != 'all':
        filters.append(f"year_{selected_year}")
    
    filename = f"financial_and_exam_report_{'_'.join(filters) if filters else 'all'}.xlsx"
    
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )




@app.route('/search_students')
@login_required
def search_students():
    search = request.args.get('search', '').strip()
    show_inactive = request.args.get('show_inactive', 'false') == 'true'
    
    # Base query
    query = Student.query
    
    # Filter by active status unless explicitly showing inactive
    if not show_inactive:
        query = query.filter(Student.active == True)
    
    # Apply search filter
    if search:
        query = query.filter(
            or_(
                Student.name.ilike(f'%{search}%'),
                Student.id.ilike(f'%{search}%')
            )
        )
    
    # Order by name
    query = query.order_by(Student.name)
    
    # Get all unique sessions and classes for filters
    sessions = db.session.query(distinct(Student.session)).order_by(Student.session).all()
    classes = db.session.query(distinct(Student.class_name)).order_by(Student.class_name).all()
    
    # Set up pagination
    page = request.args.get('page', 1, type=int)
    per_page = 50  # Number of results per page
    
    # Get paginated results
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    students = pagination.items
    
    return render_template('search_students.html', 
                         students=students,
                         pagination=pagination,
                         min=min,
                         sessions=sessions,
                         classes=classes)

# Add route for editing students
@app.route('/edit_student/<int:student_id>', methods=['GET', 'POST'])
@login_required
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)
    
    if request.method == 'POST':
        student.name = request.form['name']
        student.phone = request.form['phone']
        student.residence = request.form['residence']
        student.class_name = request.form['class']
        student.session = request.form['session']
        
        db.session.commit()
        flash('Student updated successfully', 'success')
        return redirect(url_for('search_students'))
    
    return render_template('edit_student.html', student=student)

@app.route('/exam_results')
@login_required
def exam_results():
    students = Student.query.order_by(Student.name).all()
    results = db.session.query(
        ExamResult.id,
        ExamResult.student_id,
        ExamResult.exam_type,
        ExamResult.marks_obtained,
        ExamResult.total_marks,
        ExamResult.grade,
        ExamResult.remarks,
        ExamResult.created_at,
        Student.name.label('student_name'),
        Student.class_name.label('class_name')
    ).join(Student).order_by(Student.name, ExamResult.created_at.desc()).all()
    return render_template('exam_results.html', students=students, results=results)





@app.route('/exam_result/select_student', methods=['POST'])
@login_required
def select_student_for_exam():
    student_id = request.form.get('student_id')
    if student_id:
        return redirect(url_for('add_exam_result', student_id=student_id))
    flash('Please select a student', 'error')
    return redirect(url_for('exam_results'))

def calculate_grade_and_remarks(percentage):
    """Calculate grade and remarks based on percentage"""
    if percentage >= 90:
        return 'A', 'Excellent'
    elif percentage >= 75:
        return 'B', 'Very Good'
    elif percentage >= 60:
        return 'C', 'Good'
    elif percentage >= 45:
        return 'D', 'Fair / Satisfactory'
    elif percentage >= 30:
        return 'E', 'Poor / Needs Improvement'
    else:
        return 'F', 'Fail / Unsatisfactory'

@app.route('/exam_result/edit/<int:result_id>', methods=['GET', 'POST'])
@login_required
def edit_exam_result(result_id):
    result = ExamResult.query.get_or_404(result_id)
    student = Student.query.get_or_404(result.student_id)
    
    if request.method == 'POST':
        try:
            marks_obtained = float(request.form['marks_obtained'])
            total_marks = float(request.form['total_marks'])
            
            # Validate marks
            if marks_obtained < 0 or total_marks < 0:
                raise ValueError("Marks cannot be negative")
            if marks_obtained > total_marks:
                raise ValueError("Marks obtained cannot be greater than total marks")
            
            # Calculate percentage and determine grade and remarks
            percentage = (marks_obtained / total_marks) * 100
            grade, remarks = calculate_grade_and_remarks(percentage)
            
            # Update exam result
            result.marks_obtained = marks_obtained
            result.total_marks = total_marks
            result.grade = grade
            result.remarks = remarks
            
            db.session.commit()
            
            flash('Exam result updated successfully!', 'success')
            return redirect(url_for('view_student', student_id=student.id))
            
        except ValueError as e:
            flash(f'Invalid marks: {str(e)}', 'error')
            return redirect(url_for('edit_exam_result', result_id=result_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating exam result: {str(e)}', 'error')
            return redirect(url_for('edit_exam_result', result_id=result_id))
    
    return render_template('edit_exam_result.html', result=result, student=student)

@app.route('/exam_result/add/<int:student_id>', methods=['GET', 'POST'])
@login_required
def add_exam_result(student_id):
    student = Student.query.get_or_404(student_id)
    
    if request.method == 'POST':
        try:
            exam_type = request.form['exam_type']
            marks_obtained = float(request.form['marks_obtained'])
            total_marks = float(request.form['total_marks'])
            
            # Validate marks
            if marks_obtained > total_marks:
                flash('Marks obtained cannot be greater than total marks', 'error')
                return redirect(url_for('add_exam_result', student_id=student_id))
            
            # Check if exam result already exists
            existing_result = ExamResult.query.filter_by(
                student_id=student_id,
                exam_type=exam_type
            ).first()
            
            if existing_result:
                flash(f'An exam result for {exam_type} already exists for this student', 'error')
                return redirect(url_for('add_exam_result', student_id=student_id))
            
            # Calculate percentage and determine grade and remarks
            percentage = (marks_obtained / total_marks) * 100
            grade, remarks = calculate_grade_and_remarks(percentage)
            
            # Create new exam result
            new_result = ExamResult(
                student_id=student_id,
                exam_type=exam_type,
                marks_obtained=marks_obtained,
                total_marks=total_marks,
                grade=grade,
                remarks=remarks
            )
            
            db.session.add(new_result)
            db.session.commit()
            
            flash('Exam result added successfully!', 'success')
            return redirect(url_for('view_student', student_id=student_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding exam result: {str(e)}', 'error')
            return redirect(url_for('add_exam_result', student_id=student_id))
    
    return render_template('add_exam_result.html', student=student)

@app.route('/delete_exam_result/<int:exam_result_id>', methods=['POST'])
@login_required
def delete_exam_result(exam_result_id):
    exam_result = ExamResult.query.get_or_404(exam_result_id)
    db.session.delete(exam_result)
    db.session.commit()
    flash('Exam result deleted successfully', 'success')
    return redirect(url_for('exam_results'))

@app.route('/generate_result_slip/<int:student_id>')
@login_required
def generate_result_slip(student_id):
    student = Student.query.get_or_404(student_id)
    exam_results = db.session.query(
        ExamResult.id,
        ExamResult.exam_type,
        ExamResult.marks_obtained,
        ExamResult.total_marks,
        ExamResult.grade,
        ExamResult.remarks,
        ExamResult.created_at
    ).filter(ExamResult.student_id == student_id).all()
    
    # Calculate averages
    class_midterm = next((r for r in exam_results if r.exam_type == 'class_midterm'), None)
    leadership_midterm = next((r for r in exam_results if r.exam_type == 'leadership_midterm'), None)
    class_final = next((r for r in exam_results if r.exam_type == 'class_final'), None)
    leadership_final = next((r for r in exam_results if r.exam_type == 'leadership_final'), None)
    
    # Calculate overall average
    total_percentage = 0
    count = 0
    for result in exam_results:
        percentage = (result.marks_obtained / result.total_marks) * 100
        total_percentage += percentage
        count += 1
    
    overall_average = total_percentage / count if count > 0 else 0
    
    # Get current date
    current_date = datetime.now()
    
    return render_template('result_slip.html', 
                         student=student, 
                         exam_results=exam_results,
                         class_midterm=class_midterm,
                         leadership_midterm=leadership_midterm,
                         class_final=class_final,
                         leadership_final=leadership_final,
                         overall_average=overall_average,
                         current_date=current_date)

@app.route('/view_student/<int:student_id>')
@login_required
def view_student(student_id):
    student = Student.query.get_or_404(student_id)
    
    # Calculate total paid amount
    total_paid = db.session.query(func.sum(Payment.amount)).\
        filter(Payment.student_id == student_id).scalar() or 0
    
    # Get last payment
    last_payment = Payment.query.\
        filter(Payment.student_id == student_id).\
        order_by(Payment.date.desc()).first()
    
    # Get exam results
    exam_results = ExamResult.query.filter_by(student_id=student_id).all()
    
    # Get all years for the filter
    years = db.session.query(distinct(Payment.year)).\
        filter(Payment.student_id == student_id).all()
    years = [year[0] for year in years]
    
    # Get attendance records
    attendance = Attendance.query.filter_by(student_id=student_id).\
        order_by(Attendance.date.desc()).all()
    
    return render_template('view_student.html',
                         student=student,
                         total_paid=total_paid,
                         last_payment=last_payment,
                         exam_results=exam_results,
                         years=years,
                         attendance=attendance)

@app.route('/generate_qr/student/<int:student_id>')
def generate_student_qr(student_id):
    """
    Generate QR code for student verification
    QR data: 'IYF-Student:{id}-{name}' - scans to student profile
    """
    try:
        student = Student.query.get_or_404(student_id)
        qr_data = f"IYF-Student:{student.id}-{student.name}"
        
        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save to BytesIO
        img_buffer = BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        return send_file(
            img_buffer,
            mimetype='image/png',
            as_attachment=False,
            download_name=f'student_{student_id}_qr.png'
        )
    except Exception as e:
        return "QR generation failed", 500


@app.route('/reset_db')
def reset_db():
    db.drop_all()
    db.create_all()
    return 'Database reset successfully'

if __name__ == '__main__':
    with app.app_context():
        # Create instance directory if it doesn't exist
        os.makedirs('instance', exist_ok=True)
        
        # Create database file if it doesn't exist
        db_path = os.path.join('instance', 'academy.db')
        if not os.path.exists(db_path):
            db.create_all()
            print(f"Database created at {db_path}")
        else:
            print(f"Using existing database at {db_path}")
            db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)
