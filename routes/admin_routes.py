from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
from models import db, Admin, Teacher, TeacherLogin, SubAdmin, Student
from flask_login import login_user, logout_user, login_required, UserMixin, current_user
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

        # Admin login only
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
            session['user_type'] = 'Admin'
            print(f"[DEBUG] After login: is_authenticated={admin.is_authenticated}, user={admin.username}")
            return redirect(url_for('main.index'))

        flash('Invalid username or password', 'error')
    return render_template('login.html')

@admin_routes.route('/subadmin/login', methods=['GET', 'POST'])
def subadmin_login():
    from flask_login import current_user
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # SubAdmin login only
        sub_admin = SubAdmin.query.filter_by(username=username).first()
        if sub_admin and sub_admin.active and sub_admin.check_password(password):
            login_user(sub_admin)
            session['user_type'] = 'SubAdmin'
            print(f"[DEBUG] Sub-admin login: {sub_admin.username}")
            return redirect(url_for('main.index'))

        flash('Invalid username or password', 'error')
    return render_template('login.html')

@admin_routes.route('/admin/merge_classes', methods=['GET', 'POST'])
@login_required
def merge_classes():
    # Only main admin can merge classes
    if not isinstance(current_user, Admin):
        flash('Only main admin can merge classes', 'error')
        return redirect(url_for('main.index'))

    # Get all unique class names with student counts
    class_stats = db.session.query(
        Student.class_name,
        db.func.count(Student.id).label('count')
    ).filter(
        Student.class_name.isnot(None),
        Student.class_name != ''
    ).group_by(Student.class_name).order_by(Student.class_name).all()

    # Standardized class names
    standard_classes = [
        'Computer Packages', 'Computer Programming', 'AI tool for Web design',
        'Hair and Beauty', 'Hairdressing and Beauty Therapy',
        'Caregiver', 'Paramedics',
        'Electrical Installation', 'Plumbing', 'Refrigeration',
        'Food and Beverage', 'Hospitality',
        'Sign Language', 'French', 'German',
        'Digital Marketing', 'Sales and Marketing', 'Videography', 'Tailoring', 'Taekwondo',
        'Music Instrumentals', 'Smart Agriculture', 'Barbering', 'Theology'
    ]

    if request.method == 'POST':
        target_class = request.form.get('target_class')
        classes_to_merge = request.form.getlist('classes_to_merge')

        if not target_class or not classes_to_merge:
            flash('Please select a target class and classes to merge', 'error')
        else:
            try:
                # Update all students with the selected class names to the target class
                updated_count = Student.query.filter(Student.class_name.in_(classes_to_merge)).update(
                    {'class_name': target_class},
                    synchronize_session=False
                )
                db.session.commit()
                flash(f'Successfully merged {updated_count} students into "{target_class}"', 'success')
                return redirect(url_for('admin_routes.merge_classes'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error merging classes: {str(e)}', 'error')

    return render_template('merge_classes.html', class_stats=class_stats, standard_classes=standard_classes)

@admin_routes.route('/admin/auto_fix_classes', methods=['POST'])
@login_required
def auto_fix_classes():
    # Only main admin can auto-fix classes
    if not isinstance(current_user, Admin):
        flash('Only main admin can auto-fix classes', 'error')
        return redirect(url_for('main.index'))

    # Typo mapping: typo -> correct standardized name
    typo_mapping = {
        # Computer Packages typos
        'COMPUER PARCKAGES': 'Computer Packages',
        'COMPUER PERCKAGES': 'Computer Packages',
        'COMPUTER PARCKAGES': 'Computer Packages',
        'COMPUTER': 'Computer Packages',
        'Computer': 'Computer Packages',
        'Computer Packages': 'Computer Packages',
        # Computer Programming typos
        'COMPUER PROGRAMMING': 'Computer Programming',
        'COMPUTER PROGRAMING': 'Computer Programming',
        'Computer programming': 'Computer Programming',
        'Computer Programming': 'Computer Programming',
        # AI for Web Design typos
        'AI tool for Web design': 'AI tool for Web design',
        'AI FOR WEB DESIGN': 'AI tool for Web design',
        'AI for Web Design': 'AI tool for Web design',
        # Beauty & Hairdressing typos
        'BEAUTY AND HAIRDRESSING': 'Hair and Beauty',
        'BEUTY AND HAIR DRESSING': 'Hair and Beauty',
        'Beaty': 'Hair and Beauty',
        'Beauty': 'Hair and Beauty',
        'HAIR AND BEAUT': 'Hair and Beauty',
        'HAIR AND BEAUTY': 'Hair and Beauty',
        'HAIR DRESSING': 'Hair and Beauty',
        'Hair and Beauty': 'Hair and Beauty',
        'Hair and beauty': 'Hair and Beauty',
        'Hairdressing and Beauty': 'Hair and Beauty',
        'BEAUTY AND THERAPY': 'Hair and Beauty',
        'Hair and Beauty': 'Hair and Beauty',
        'COSMETOLOGY': 'Hair and Beauty',
        'Cosmetology': 'Hair and Beauty',
        'Hairdressing and Beauty Therapy': 'Hairdressing and Beauty Therapy',
        # Caregiver typos
        'CARE GIVER': 'Caregiver',
        'Care giver': 'Caregiver',
        'Caregiver': 'Caregiver',
        'CAREGIVER COURSE': 'Caregiver',
        'CAREGIVER': 'Caregiver',
        # Paramedics typos
        'PARAMEDIC': 'Paramedics',
        'Paramedic': 'Paramedics',
        'PAREMEDICS': 'Paramedics',
        'Paramedics': 'Paramedics',
        # Electrical Installation typos
        'Electrical': 'Electrical Installation',
        'ELECTRICAL': 'Electrical Installation',
        'Electrical installation': 'Electrical Installation',
        'ELECTRICAL INSTALLATION': 'Electrical Installation',
        'Electrical Installation': 'Electrical Installation',
        # Plumbing typos
        'Plumbing': 'Plumbing',
        'PLUMBING': 'Plumbing',
        # Refrigeration typos
        'BASIC REFRIGERATION': 'Refrigeration',
        'REFRIGERATION': 'Refrigeration',
        'Refrigeration': 'Refrigeration',
        # Food and Beverage typos
        'FOOD AND BEVERAGE': 'Food and Beverage',
        'Food and Beverage': 'Food and Beverage',
        'Food and beverage': 'Food and Beverage',
        # Hospitality typos
        'HOSPITALITY': 'Hospitality',
        'Hospitality': 'Hospitality',
        # Sign Language typos
        'SIGN LANGUAGE': 'Sign Language',
        'Sign language advance': 'Sign Language',
        'Sign Language': 'Sign Language',
        'BASIC SIGN LANGUAGE': 'Sign Language',
        'ADVANCED SIGN LANGUAGE': 'Sign Language',
        # French typos
        'FRENCH': 'French',
        'French': 'French',
        # German typos
        'GERMAN': 'German',
        'GERMAN CLASSES': 'German',
        'German': 'German',
        'Germany': 'German',
        # Digital Marketing typos
        'DIGITAL MARKETING': 'Digital Marketing',
        'Digital Marketing': 'Digital Marketing',
        # Sales and Marketing typos
        'SALES AND MARKETING': 'Sales and Marketing',
        'SALES MARKETING': 'Sales and Marketing',
        'Sales Marketing': 'Sales and Marketing',
        'MARKETING': 'Sales and Marketing',
        # Videography typos
        'VIDEOGRAPHY': 'Videography',
        'Videography': 'Videography',
        # Tailoring typos
        'TAILORING': 'Tailoring',
        'Tailoring': 'Tailoring',
        # Taekwondo typos
        'TAEKWONDO': 'Taekwondo',
        'TAYQOUNDO': 'Taekwondo',
        'Taekwondo': 'Taekwondo',
        # Music typos
        'MUSIC': 'Music Instrumentals',
        'MUSIC INSTRUMENTALS': 'Music Instrumentals',
        # Smart Agriculture typos
        'SMART AGRICULTURE': 'Smart Agriculture',
        # Barbering typos
        'BARBERING': 'Barbering',
        # Theology typos
        'THEOLOGY': 'Theology',
        # Other
        'ENTERPRENUERSHIP': 'Digital Marketing',
        'College': 'Computer Packages',
        'Campus': 'Computer Packages',
        'Tertiary': 'Computer Packages',
        'Diploma': 'Computer Packages',
        'Form 4': 'Computer Packages',
    }

    try:
        total_updated = 0
        for typo, correct_name in typo_mapping.items():
            count = Student.query.filter(Student.class_name == typo).update(
                {'class_name': correct_name},
                synchronize_session=False
            )
            if count > 0:
                total_updated += count

        db.session.commit()
        flash(f'Successfully auto-fixed {total_updated} students with typo corrections', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error auto-fixing classes: {str(e)}', 'error')

    return redirect(url_for('admin_routes.merge_classes'))

@admin_routes.route('/admin/edit_teacher/<int:teacher_id>', methods=['GET', 'POST'])
@login_required
def edit_teacher(teacher_id):
    # Only main admin can edit teachers
    if not isinstance(current_user, Admin):
        flash('Only main admin can edit teachers', 'error')
        return redirect(url_for('main.index'))

    teacher = Teacher.query.get_or_404(teacher_id)

    if request.method == 'POST':
        teacher.first_name = request.form['first_name']
        teacher.last_name = request.form['last_name']
        teacher.email = request.form['email']
        teacher.phone = request.form['phone']
        teacher.qualification = request.form['qualification']
        teacher.subject = request.form['subject']
        teacher.class_name = request.form.get('class_name', '')

        # Check if email already exists for another teacher
        existing_teacher = Teacher.query.filter_by(email=request.form['email']).first()
        if existing_teacher and existing_teacher.id != teacher_id:
            flash(f'A teacher with email "{request.form["email"]}" already exists. Please use a different email address.', 'error')
            return render_template('edit_teacher.html', teacher=teacher)

        db.session.commit()
        flash('Teacher updated successfully', 'success')
        return redirect(url_for('admin_routes.manage_teachers'))

    return render_template('edit_teacher.html', teacher=teacher)

@admin_routes.route('/admin/add_teacher', methods=['GET', 'POST'])
@login_required
def add_teacher():
    # Only main admin can add teachers
    if not isinstance(current_user, Admin):
        flash('Only main admin can add teachers', 'error')
        return redirect(url_for('main.index'))

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
    # Only main admin can manage teachers
    if not isinstance(current_user, Admin):
        flash('Only main admin can manage teachers', 'error')
        return redirect(url_for('main.index'))
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
    # Only main admin can delete teachers
    if not isinstance(current_user, Admin):
        flash('Only main admin can delete teachers', 'error')
        return redirect(url_for('main.index'))
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
    # Only main admin can toggle teacher status
    if not isinstance(current_user, Admin):
        flash('Only main admin can manage teachers', 'error')
        return redirect(url_for('main.index'))
    teacher = Teacher.query.get_or_404(teacher_id)
    teacher.active = not teacher.active
    db.session.commit()
    status = "activated" if teacher.active else "deactivated"
    flash(f'Teacher "{teacher.first_name} {teacher.last_name}" has been {status} successfully.', 'success')
    return redirect(url_for('admin_routes.manage_teachers'))

@admin_routes.route('/admin/send_credentials/<int:teacher_id>', methods=['POST'])
@login_required
def send_teacher_credentials(teacher_id):
    # Only main admin can send teacher credentials
    if not isinstance(current_user, Admin):
        flash('Only main admin can send teacher credentials', 'error')
        return redirect(url_for('main.index'))
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
    from flask import session
    user_type = session.get('user_type')
    session.clear()
    logout_user()
    # Redirect to appropriate login page based on user type
    if user_type == 'SubAdmin':
        return redirect(url_for('admin_routes.subadmin_login'))
    return redirect(url_for('admin_routes.admin_login'))

@admin_routes.route('/admin/manage-exams')
@login_required
def manage_exams():
    """Route for admins to view and print teacher-uploaded exams"""
    # Only main admin can manage exams
    if not isinstance(current_user, Admin):
        flash('Only main admin can manage exams', 'error')
        return redirect(url_for('main.index'))
    # For now, return a placeholder page
    # In the future, this will query a database of uploaded exams
    return render_template('admin_manage_exams.html')

@admin_routes.route('/admin/add-subadmin', methods=['GET', 'POST'])
@login_required
def add_subadmin():
    """Route for main admin to add sub-admins"""
    # Only main admin can add sub-admins
    if not isinstance(current_user, Admin):
        flash('Only main admin can add sub-admins', 'error')
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')

        if not all([username, full_name, password]):
            flash('Username, full name, and password are required', 'error')
            return render_template('add_subadmin.html')

        # Check if username already exists
        existing_subadmin = SubAdmin.query.filter_by(username=username).first()
        if existing_subadmin:
            flash(f'Sub-admin with username "{username}" already exists', 'error')
            return render_template('add_subadmin.html')

        try:
            sub_admin = SubAdmin(
                username=username,
                full_name=full_name,
                email=email,
                created_by=current_user.id,
                active=True
            )
            sub_admin.set_password(password)
            db.session.add(sub_admin)
            db.session.commit()

            flash(f'Sub-admin "{username}" added successfully!', 'success')
            return redirect(url_for('admin_routes.manage_subadmins'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding sub-admin: {str(e)}', 'error')

    return render_template('add_subadmin.html')

@admin_routes.route('/admin/subadmins')
@login_required
def manage_subadmins():
    """Route for main admin to view and manage sub-admins"""
    if not isinstance(current_user, Admin):
        flash('Only main admin can manage sub-admins', 'error')
        return redirect(url_for('main.index'))

    subadmins = SubAdmin.query.order_by(SubAdmin.created_at.desc()).all()
    return render_template('manage_subadmins.html', subadmins=subadmins)

@admin_routes.route('/admin/delete-subadmin/<int:subadmin_id>', methods=['POST'])
@login_required
def delete_subadmin(subadmin_id):
    """Route for main admin to delete sub-admins"""
    if not isinstance(current_user, Admin):
        flash('Only main admin can delete sub-admins', 'error')
        return redirect(url_for('main.index'))

    sub_admin = SubAdmin.query.get_or_404(subadmin_id)
    db.session.delete(sub_admin)
    db.session.commit()
    flash(f'Sub-admin "{sub_admin.username}" has been deleted', 'success')
    return redirect(url_for('admin_routes.manage_subadmins'))

@admin_routes.route('/admin/toggle-subadmin/<int:subadmin_id>', methods=['POST'])
@login_required
def toggle_subadmin_status(subadmin_id):
    """Route for main admin to activate/deactivate sub-admins"""
    if not isinstance(current_user, Admin):
        flash('Only main admin can manage sub-admins', 'error')
        return redirect(url_for('main.index'))

    sub_admin = SubAdmin.query.get_or_404(subadmin_id)
    sub_admin.active = not sub_admin.active
    db.session.commit()
    status = "activated" if sub_admin.active else "deactivated"
    flash(f'Sub-admin "{sub_admin.username}" has been {status}', 'success')
    return redirect(url_for('admin_routes.manage_subadmins'))
