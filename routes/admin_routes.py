from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from models import db, Admin, Teacher, TeacherLogin
from flask_login import login_user, logout_user, login_required, UserMixin
from flask_mail import Message
from werkzeug.security import generate_password_hash
import secrets

admin_routes = Blueprint('admin_routes', __name__,
                        template_folder='../templates',
                        static_folder='../static')



@admin_routes.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    from flask_login import current_user
    print(f"[DEBUG] Before login: is_authenticated={current_user.is_authenticated}, user={getattr(current_user, 'username', None)}")
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        admin = Admin.query.filter_by(username=username).first()
        print(f"[DEBUG] Admin lookup: admin={admin}")
        if admin:
            # Check if password hash uses unsupported scrypt method
            if admin.password_hash and admin.password_hash.startswith('scrypt'):
                print(f"[DEBUG] Detected scrypt hash, auto-resetting password to: {password}")
                admin.set_password(password)
                db.session.commit()
                print(f"[DEBUG] Password hash updated to supported algorithm")
            print(f"[DEBUG] Password check: {admin.check_password(password)}")
        if admin and admin.check_password(password):
            login_user(admin)  # Use the actual Admin model instance
            print(f"[DEBUG] After login: is_authenticated={admin.is_authenticated}, user={admin.username}")
            return redirect(url_for('main.index'))
        else:
            flash('Invalid admin username or password', 'error')
    return render_template('login.html')

@admin_routes.route('/admin/add_teacher', methods=['GET', 'POST'])
@login_required
def add_teacher():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        phone = request.form['phone']
        qualification = request.form['qualification']
        subject = request.form['subject']
        
        # Check if email already exists
        existing_teacher = Teacher.query.filter_by(email=email).first()
        if existing_teacher:
            flash(f'A teacher with email "{email}" already exists. Please use a different email address.', 'error')
            return render_template('add_teacher.html')
        
        from werkzeug.security import generate_password_hash
        import secrets
        password = secrets.token_urlsafe(12)
        password_hash = generate_password_hash(password)
        
        username = email
        
        try:
            teacher = Teacher(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                class_name=request.form.get('class_name', ''),
                subject=subject,
                qualification=qualification,
                active=True
            )
            db.session.add(teacher)
            db.session.flush()
            
            login = TeacherLogin(
                teacher_id=teacher.id,
                username=username,
                password_hash=password_hash
            )
            db.session.add(login)
            db.session.commit()

            # Auto-sync to Supabase
            try:
                from supabase_sync import sync_teacher_to_supabase, sync_teacher_login_to_supabase
                sync_teacher_to_supabase(teacher)
                sync_teacher_login_to_supabase(login)
            except Exception as e:
                print(f"Supabase sync error: {str(e)}")

            flash(f'Teacher added! Username: {username}, Temp Password: {password}', 'success')
            return redirect(url_for('main.index'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while adding the teacher: {str(e)}', 'error')
            return render_template('add_teacher.html')
    
    return render_template('add_teacher.html')

@admin_routes.route('/admin/teachers')
@login_required
def manage_teachers():
    from datetime import datetime
    teachers = Teacher.query.order_by(Teacher.created_at.desc()).all()
    active_count = len([t for t in teachers if t.active])
    inactive_count = len(teachers) - active_count
    current_month = datetime.now().strftime('%Y-%m')
    new_this_month = len([t for t in teachers if t.created_at and t.created_at.strftime('%Y-%m') == current_month])
    return render_template('manage_teachers.html', teachers=teachers, active_count=active_count, inactive_count=inactive_count, new_this_month=new_this_month)

@admin_routes.route('/admin/delete_teacher/<int:teacher_id>', methods=['POST'])
@login_required
def delete_teacher(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    # Delete teacher_login record first to avoid NOT NULL constraint
    teacher_login = TeacherLogin.query.filter_by(teacher_id=teacher_id).first()
    if teacher_login:
        db.session.delete(teacher_login)
    db.session.delete(teacher)
    db.session.commit()
    flash(f'Teacher "{teacher.first_name} {teacher.last_name}" has been deleted successfully.', 'success')
    return redirect(url_for('admin_routes.manage_teachers'))

@admin_routes.route('/admin/toggle_teacher/<int:teacher_id>', methods=['POST'])
@login_required
def toggle_teacher_status(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    teacher.active = not teacher.active
    db.session.commit()
    status = "activated" if teacher.active else "deactivated"
    flash(f'Teacher "{teacher.first_name} {teacher.last_name}" has been {status} successfully.', 'success')
    return redirect(url_for('admin_routes.manage_teachers'))

@admin_routes.route('/admin/send_credentials/<int:teacher_id>', methods=['POST'])
@login_required
def send_teacher_credentials(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    teacher_login = TeacherLogin.query.filter_by(teacher_id=teacher_id).first()

    if teacher_login:
        # Generate new temporary password
        import secrets
        from werkzeug.security import generate_password_hash
        new_password = secrets.token_urlsafe(12)
        teacher_login.password_hash = generate_password_hash(new_password)
        db.session.commit()

        # Send email with credentials
        try:
            msg = Message(
                subject='Your Teacher Account Credentials - IYF FREE WEEKEND ACADEMY',
                recipients=[teacher.email],
                html=f'''
                <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #2563eb;">Welcome to IYF FREE WEEKEND ACADEMY</h2>
                        <p>Dear {teacher.first_name} {teacher.last_name},</p>
                        <p>Your teacher account has been created/updated. Below are your login credentials:</p>
                        <div style="background: #f3f4f6; padding: 15px; border-radius: 5px; margin: 20px 0;">
                            <p><strong>Username:</strong> {teacher_login.username}</p>
                            <p><strong>Temporary Password:</strong> {new_password}</p>
                        </div>
                        <p>Please log in at: <a href="http://127.0.0.1:5000/teacher/login" style="color: #2563eb;">http://127.0.0.1:5000/teacher/login</a></p>
                        <p><strong>Important:</strong> Please change your password after your first login for security.</p>
                        <p>If you did not request this, please contact the administrator immediately.</p>
                        <p>Best regards,<br>IYF FREE WEEKEND ACADEMY Administration</p>
                    </div>
                </body>
                </html>
                '''
            )
            current_app.mail.send(msg)
            flash(f'Credentials sent to {teacher.email}. Please check their inbox.', 'success')
        except Exception as e:
            flash(f'Failed to send email: {str(e)}. Temporary password: {new_password}', 'error')
    else:
        flash('Teacher login credentials not found.', 'error')

    return redirect(url_for('admin_routes.manage_teachers'))

@admin_routes.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for('admin_routes.admin_login'))

@admin_routes.route('/admin/manage-exams')
@login_required
def manage_exams():
    """Route for admins to view and print teacher-uploaded exams"""
    # For now, return a placeholder page
    # In the future, this will query a database of uploaded exams
    return render_template('admin_manage_exams.html')
