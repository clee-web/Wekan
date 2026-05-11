from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
from models import db, Admin, Teacher, TeacherLogin, SubAdmin, Student
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from werkzeug.security import generate_password_hash
from datetime import datetime
import secrets

admin_routes = Blueprint(
    'admin_routes',
    __name__,
    template_folder='../templates',
    static_folder='../static'
)

# =========================
# ADMIN LOGOUT (FIXED)
# =========================
@admin_routes.route('/admin/logout')
@login_required
def admin_logout():
    """
    Logs out Admin or SubAdmin safely
    and redirects to correct login page.
    """

    user_type = session.get('user_type')

    session.clear()
    logout_user()

    if user_type == 'SubAdmin':
        return redirect(url_for('admin_routes.subadmin_login'))

    return redirect(url_for('admin_routes.admin_login'))


# =========================
# ADMIN LOGIN
# =========================
@admin_routes.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    from flask_login import current_user

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == 'admin' and password == 'adminiyf':
            admin = Admin.query.filter_by(username='admin').first()

            if not admin:
                admin = Admin(username='admin')
                admin.set_password('adminiyf')
                db.session.add(admin)
                db.session.commit()

            login_user(admin)
            session['user_type'] = 'Admin'
            flash('Logged in (hardcoded mode)', 'success')
            return redirect(url_for('main.index'))

        admin = Admin.query.filter_by(username=username).first()

        if admin and admin.check_password(password):
            login_user(admin)
            session['user_type'] = 'Admin'
            return redirect(url_for('main.index'))

        flash('Invalid credentials', 'error')

    return render_template('login.html')


# =========================
# SUBADMIN LOGIN
# =========================
@admin_routes.route('/subadmin/login', methods=['GET', 'POST'])
def subadmin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        sub_admin = SubAdmin.query.filter_by(username=username).first()

        if sub_admin and sub_admin.active and sub_admin.check_password(password):
            login_user(sub_admin)
            session['user_type'] = 'SubAdmin'
            return redirect(url_for('main.index'))

        flash('Invalid username or password', 'error')

    return render_template('login.html')


# =========================
# TEACHER MANAGEMENT ROUTES
# =========================
from models import Teacher
from flask_login import login_required
from datetime import datetime, timedelta


@admin_routes.route('/manage_teachers')
@login_required
def manage_teachers():
    """Display all teachers with stats"""
    teachers = Teacher.query.all()
    
    active_count = Teacher.query.filter_by(active=True).count()
    inactive_count = Teacher.query.filter_by(active=False).count()
    new_this_month = Teacher.query.filter(
        Teacher.created_at >= datetime.now() - timedelta(days=30)
    ).count()
    
    return render_template('manage_teachers.html',
                         teachers=teachers,
                         active_count=active_count,
                         inactive_count=inactive_count,
                         new_this_month=new_this_month)


@admin_routes.route('/add_teacher', methods=['GET', 'POST'])
@login_required
def add_teacher():
    if request.method == 'POST':
        flash('Teacher creation feature coming soon!', 'info')
        return redirect(url_for('admin_routes.manage_teachers'))
    return render_template('add_teacher.html')


@admin_routes.route('/edit_teacher/<int:teacher_id>', methods=['GET', 'POST'])
@login_required
def edit_teacher(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    if request.method == 'POST':
        flash('Teacher update feature coming soon!', 'info')
        return redirect(url_for('admin_routes.manage_teachers'))
    return render_template('edit_teacher.html', teacher=teacher)


@admin_routes.route('/send_teacher_credentials/<int:teacher_id>', methods=['POST'])
@login_required
def send_teacher_credentials(teacher_id):
    flash('Email credentials feature coming soon!', 'info')
    return redirect(url_for('admin_routes.manage_teachers'))


@admin_routes.route('/toggle_teacher_status/<int:teacher_id>', methods=['POST'])
@login_required
def toggle_teacher_status(teacher_id):
    flash('Toggle status feature coming soon!', 'info')
    return redirect(url_for('admin_routes.manage_teachers'))


@admin_routes.route('/delete_teacher/<int:teacher_id>', methods=['POST'])
@login_required
def delete_teacher(teacher_id):
    flash('Delete teacher feature coming soon!', 'info')
    return redirect(url_for('admin_routes.manage_teachers'))


# =========================
# ADDITIONAL STUB ROUTES FOR DASHBOARD
# =========================


@admin_routes.route('/merge_classes', methods=['GET', 'POST'])
@login_required
def merge_classes():
    """Merge classes page (GET) + run merge/fix (POST)."""
    if request.method == 'POST':
        action = request.form.get('action')
        # If templates don't pass action, infer from which submit button exists.
        if not action:
            action = 'merge'

        try:
            # Use the existing SQLite helper script logic
            from merge_classes import merge_classes as run_merge_classes
            from merge_classes import merge_sessions
            from merge_classes import normalize_class_name

            if action == 'fix_typos':
                # Keep simple: first merge session variants then merge class variants
                merge_sessions()
                run_merge_classes()
                flash('Class names auto-fixed successfully.', 'success')
            else:
                merge_sessions()
                run_merge_classes()
                flash('Classes merged successfully.', 'success')
        except Exception as e:
            flash(f'Failed to merge/fix classes: {e}', 'error')

        return redirect(url_for('admin_routes.merge_classes'))

    # GET
    return render_template('merge_classes.html')



@admin_routes.route('/manage_subadmins')
@login_required
def manage_subadmins():
    """Manage subadmins page"""
    return render_template('manage_subadmins.html')


@admin_routes.route('/add_subadmin', methods=['GET', 'POST'])
@login_required
def add_subadmin():
    """Add subadmin stub"""
    if request.method == 'POST':
        flash('Subadmin creation coming soon!', 'info')
        return redirect(url_for('admin_routes.manage_subadmins'))
    return render_template('add_subadmin.html')
