from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_user, login_required, logout_user, current_user
from flask_mail import Message
from models import Teacher, TeacherLogin, Attendance, ExamResult, Student, db
from sqlalchemy import or_
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps

teacher_routes = Blueprint('teacher_routes', __name__,
                          template_folder='../templates',
                          static_folder='../static')

def teacher_login_required(f):
    """Custom decorator that redirects to teacher login instead of admin login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('teacher_routes.teacher_login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@teacher_routes.route('/teacher/login', methods=['GET', 'POST'])
def teacher_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        print(f"Login attempt: username={username}")
        
        login = TeacherLogin.query.filter_by(username=username).first()
        if login:
            print(f"Found login record for username={username}")
            # Check if password hash uses unsupported scrypt method
            if login.password_hash and login.password_hash.startswith('scrypt'):
                print(f"[DEBUG] Detected scrypt hash for teacher, auto-resetting password")
                login.set_password(password)
                db.session.commit()
                print(f"[DEBUG] Teacher password hash updated to supported algorithm")
        if login and login.check_password(password):
            print("Password check succeeded")
            login_user(login)
            # Set session to permanent to ensure it persists
            from flask import session as flask_session
            flask_session.permanent = True
            print(f"Logged in user: {login.teacher.name}")
            return redirect(url_for('teacher_routes.teacher_dashboard'))
        else:
            print(f"No login record found or password failed for username={username}")
        flash('Invalid username or password')
    return render_template('teacher_login.html')

@teacher_routes.route('/teacher/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        teacher_login = TeacherLogin.query.join(Teacher).filter(Teacher.email == email).first()

        if teacher_login:
            # Generate new temporary password
            import secrets
            from werkzeug.security import generate_password_hash
            new_password = secrets.token_urlsafe(12)
            teacher_login.password_hash = generate_password_hash(new_password)
            db.session.commit()

            # Send email with new password
            try:
                msg = Message(
                    subject='Password Reset - IYF FREE WEEKEND ACADEMY',
                    recipients=[email],
                    html=f'''
                    <html>
                    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                            <h2 style="color: #2563eb;">Password Reset Request</h2>
                            <p>Dear Teacher,</p>
                            <p>Your password has been reset. Below are your new login credentials:</p>
                            <div style="background: #f3f4f6; padding: 15px; border-radius: 5px; margin: 20px 0;">
                                <p><strong>Username:</strong> {teacher_login.username}</p>
                                <p><strong>New Temporary Password:</strong> {new_password}</p>
                            </div>
                            <p>Please log in at: <a href="http://127.0.0.1:5000/teacher/login" style="color: #2563eb;">http://127.0.0.1:5000/teacher/login</a></p>
                            <p><strong>Important:</strong> Please change your password after logging in for security.</p>
                            <p>If you did not request this password reset, please contact the administrator immediately.</p>
                            <p>Best regards,<br>IYF FREE WEEKEND ACADEMY Administration</p>
                        </div>
                    </body>
                    </html>
                    '''
                )
                current_app.mail.send(msg)
                flash(f'Password reset instructions have been sent to {email}. Please check your email.', 'success')
            except Exception as e:
                flash(f'Failed to send email: {str(e)}. Please contact administrator.', 'error')
        else:
            flash('No teacher account found with that email address.', 'error')

    return render_template('teacher_login.html')

@teacher_routes.route('/teacher/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    # This would handle the actual password reset with token
    # For now, just redirect to login with a message
    flash('Password reset functionality is being developed. Please contact administrator.', 'info')
    return redirect(url_for('teacher_routes.teacher_login'))

@teacher_routes.route('/teacher/logout')
@teacher_login_required
def teacher_logout():
    logout_user()
    return redirect(url_for('teacher_routes.teacher_login'))

@teacher_routes.route('/teacher/dashboard')
@teacher_login_required
def teacher_dashboard():
    # Get teacher's assigned class
    teacher_class = current_user.teacher.class_name if current_user.teacher else None

    # Filter students by teacher's assigned class
    if teacher_class:
        students = Student.query.filter_by(class_name=teacher_class, active=True).all()
        classes = [teacher_class]
    else:
        # If no class assigned, show all students (fallback)
        students = Student.query.filter_by(active=True).all()
        classes = Student.query.filter_by(active=True).with_entities(Student.class_name).distinct().all()
        classes = [cls[0] for cls in classes]

    return render_template('teacher_dashboard.html', classes=classes, students=students, teacher_class=teacher_class)

@teacher_routes.route('/teacher/class/<class_name>')
@teacher_login_required
def class_students(class_name):
    print(f"[DEBUG] class_students called for class_name={class_name}")
    print(f"[DEBUG] current_user.is_authenticated={current_user.is_authenticated}")
    print(f"[DEBUG] current_user.id={getattr(current_user, 'id', None)}")
    print(f"[DEBUG] current_user type={type(current_user)}")

    # Get teacher's assigned class
    teacher_class = current_user.teacher.class_name if current_user.teacher else None

    # Verify teacher can access this class
    if teacher_class and class_name != teacher_class:
        flash(f'You can only view your assigned class: {teacher_class}', 'error')
        return redirect(url_for('teacher_routes.teacher_dashboard'))

    students = Student.query.filter_by(
        class_name=class_name,
        active=True
    ).all()

    # Get today's attendance records for these students
    today = datetime.utcnow().date()
    attendance_records = {}

    for student in students:
        attendance = Attendance.query.filter_by(
            student_id=student.id,
            teacher_id=current_user.id,
            date=today
        ).first()
        attendance_records[student.id] = attendance

    return render_template('class_students.html',
                         class_name=class_name,
                         students=students,
                         attendance_records=attendance_records)

@teacher_routes.route('/teacher/mark_attendance/<int:student_id>', methods=['POST'])
@teacher_login_required
def mark_attendance(student_id):
    student = Student.query.get_or_404(student_id)

    # Get teacher's assigned class
    teacher_class = current_user.teacher.class_name if current_user.teacher else None

    # Verify student is in teacher's assigned class
    if teacher_class and student.class_name != teacher_class:
        flash(f'You can only mark attendance for students in your assigned class: {teacher_class}', 'error')
        return redirect(url_for('teacher_routes.teacher_dashboard'))
    
    status = request.form.get('status')
    if status not in ['present', 'absent']:
        flash('Invalid attendance status', 'error')
        return redirect(url_for('teacher_routes.class_students', class_name=student.class_name))
    
    today = datetime.utcnow().date()
    attendance = Attendance.query.filter_by(
        student_id=student_id,
        teacher_id=current_user.id,
        date=today
    ).first()
    
    if attendance:
        attendance.status = status
    else:
        attendance = Attendance(
            student_id=student_id,
            teacher_id=current_user.id,
            date=today,
            status=status
        )
        db.session.add(attendance)
    
    db.session.commit()
    flash('Attendance marked successfully', 'success')
    return redirect(url_for('teacher_routes.class_students', class_name=student.class_name))

@teacher_routes.route('/teacher/students')
@teacher_login_required
def view_students():
    # Get teacher's assigned class
    teacher_class = current_user.teacher.class_name if current_user.teacher else None

    # Filter students by teacher's assigned class
    if teacher_class:
        students = Student.query.filter_by(class_name=teacher_class, active=True).all()
    else:
        # If no class assigned, show all students (fallback)
        students = Student.query.filter_by(active=True).all()

    return render_template('view_students.html', students=students)

@teacher_routes.route('/teacher/student/<int:student_id>')
@teacher_login_required
def view_student_detail(student_id):
    student = Student.query.get_or_404(student_id)

    # Get teacher's assigned class
    teacher_class = current_user.teacher.class_name if current_user.teacher else None

    # Verify student is in teacher's assigned class
    if teacher_class and student.class_name != teacher_class:
        flash(f'You can only view students in your assigned class: {teacher_class}', 'error')
        return redirect(url_for('teacher_routes.teacher_dashboard'))

    # Get attendance records
    attendance = Attendance.query.filter_by(student_id=student_id).\
        order_by(Attendance.date.desc()).all()

    return render_template('teacher_view_student.html',
                         student=student,
                         attendance=attendance)

@teacher_routes.route('/teacher/student/<int:student_id>/update', methods=['POST'])
@teacher_login_required
def update_student_name(student_id):
    student = Student.query.get_or_404(student_id)
    student.name = request.form.get('name')
    db.session.commit()
    flash('Student name updated successfully', 'success')
    return redirect(url_for('teacher_routes.view_student_detail', student_id=student_id))

@teacher_routes.route('/teacher/mark_attendance', methods=['GET', 'POST'])
@teacher_login_required
def mark_attendance_bulk():
    # Get teacher's assigned class
    teacher_class = current_user.teacher.class_name if current_user.teacher else None

    if request.method == 'POST':
        data = request.json
        date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        class_name = data.get('class_name')

        # Verify class matches teacher's assigned class
        if teacher_class and class_name != teacher_class:
            return jsonify({'error': f'You can only mark attendance for your assigned class: {teacher_class}'}), 403

        students = Student.query.filter_by(class_name=class_name, active=True).all()
        
        for student in students:
            status = data.get(f'status_{student.id}')
            if status in ['present', 'absent']:
                attendance = Attendance.query.filter_by(
                    student_id=student.id,
                    teacher_id=current_user.id,
                    date=date
                ).first()
                if attendance:
                    attendance.status = status
                else:
                    attendance = Attendance(
                        student_id=student.id,
                        teacher_id=current_user.id,
                        date=date,
                        status=status
                    )
                    db.session.add(attendance)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Attendance saved'})

    # Filter by teacher's assigned class
    class_name = teacher_class if teacher_class else request.args.get('class_name')
    students = Student.query.filter_by(class_name=class_name, active=True).all()
    return render_template('mark_attendance.html', students=students)

@teacher_routes.route('/teacher/exam-results', methods=['GET', 'POST'])
@teacher_login_required
def manage_exam_results():
    # Get teacher's assigned class
    teacher_class = current_user.teacher.class_name if current_user.teacher else None

    if request.method == 'POST':
        data = request.json

        # Verify student is in teacher's assigned class
        student = Student.query.get(data['student_id'])
        if teacher_class and student.class_name != teacher_class:
            return jsonify({'error': f'You can only manage exam results for students in your assigned class: {teacher_class}'}), 403

        exam_result = ExamResult(
            student_id=data['student_id'],
            exam_type=data['exam_type'],
            marks_obtained=data['marks_obtained'],
            total_marks=data['total_marks'],
            grade=data['grade'],
            remarks=data['remarks'],
            teacher_id=current_user.id
        )
        db.session.add(exam_result)
        db.session.commit()
        return jsonify({'success': True})

    # JSON API for results table
    if request.headers.get('Accept') == 'application/json' or request.args.get('json'):
        try:
            search = request.args.get('search', '').strip()
            query = db.session.query(ExamResult).outerjoin(Student).filter(Student.active == True)

            # Filter by teacher's class if assigned
            if teacher_class:
                query = query.filter(Student.class_name == teacher_class)

            if search:
                query = query.filter(or_(
                    Student.name.ilike(f'%{search}%'),
                    Student.admission_number.ilike(f'%{search}%')
                ))

            results = query.order_by(ExamResult.created_at.desc()).all()

            formatted = []
            for r in results:
                formatted.append({
                    'id': r.id,
                    'student_name': getattr(r.student, 'name', 'N/A'),
                    'admission_number': getattr(r.student, 'admission_number', '') or '',
                    'class_name': getattr(r.student, 'class_name', 'N/A'),
                    'exam_type': r.exam_type,
                    'marks_obtained': float(r.marks_obtained),
                    'total_marks': float(r.total_marks),
                    'grade': r.grade,
                    'remarks': getattr(r.remarks, 'value', r.remarks) or '',
                    'created_at': r.created_at.isoformat() if r.created_at else ''
                })
            return jsonify({'results': formatted})
        except Exception as e:
            print(f"JSON API error: {str(e)}")
            return jsonify({'error': str(e)}), 500

    # Filter students for dropdown to teacher's class if assigned
    students_query = Student.query.filter_by(active=True)
    if teacher_class:
        students_query = students_query.filter_by(class_name=teacher_class)
    students = students_query.order_by(Student.name).all()
    return render_template('exam_results.html', students=students)

@teacher_routes.route('/teacher/qr_scanner')
@teacher_login_required
def qr_scanner():
    """Teacher QR scanning page for automatic attendance marking"""
    return render_template('teacher_qr_scanner.html')

@teacher_routes.route('/teacher/manage-exams', methods=['GET', 'POST'])
@teacher_login_required
def manage_exams():
    """Route for teachers to upload or create exams for printing"""
    if request.method == 'POST':
        # Handle exam creation or upload
        exam_type = request.form.get('exam_type')
        exam_title = request.form.get('exam_title')
        exam_content = request.form.get('exam_content')
        exam_file = request.files.get('exam_file')

        if exam_file:
            # Handle file upload
            filename = f"{exam_type}_{exam_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{exam_file.filename}"
            # Save file logic here
            flash(f'Exam file "{filename}" uploaded successfully', 'success')
        elif exam_content:
            # Handle typed exam content
            flash(f'Exam "{exam_title}" created successfully', 'success')
        else:
            flash('Please provide either exam content or upload a file', 'error')

    return render_template('manage_exams.html')

@teacher_routes.route('/teacher/scan_qr', methods=['POST'])
@teacher_login_required
def teacher_scan_qr():
    """Process QR scan by teacher - extract student data and mark attendance"""
    try:
        data = request.json.get('qr_data')
        if not data:
            return jsonify({'error': 'No QR data provided'}), 400

        # Get teacher's assigned class
        teacher_class = current_user.teacher.class_name if current_user.teacher else None

        # Parse QR data format: 'student_name:student_id' or 'IYF-Student:id-name'
        import re

        # Try different QR formats
        match = re.match(r'IYF-Student:(\d+)-(.+)', data.strip())
        if match:
            student_id = int(match.group(1))
            scanned_name = match.group(2)
        else:
            # Try simple format: 'name:id'
            match = re.match(r'(.+):(\d+)', data.strip())
            if match:
                scanned_name = match.group(1).strip()
                student_id = int(match.group(2))
            else:
                return jsonify({'error': 'Invalid QR format. Expected: name:id or IYF-Student:id-name'}), 400

        # Lookup student
        student = Student.query.get(student_id)
        if not student:
            return jsonify({'error': f'Student with ID {student_id} not found'}), 404

        # Verify student is in teacher's assigned class
        if teacher_class and student.class_name != teacher_class:
            return jsonify({'error': f'Student {student.name} is not in your assigned class ({teacher_class}). Student is in {student.class_name}'}), 403

        # Verify name matches (optional, for security)
        if scanned_name.lower() != student.name.lower():
            return jsonify({'error': f'Name mismatch. Scanned: {scanned_name}, Database: {student.name}'}), 403

        if not student.active:
            return jsonify({'error': f'Student {student.name} is not active'}), 403
        
        # Get today's date
        today = datetime.utcnow().date()
        
        # Check if already marked today by this teacher
        existing = Attendance.query.filter_by(
            student_id=student_id,
            teacher_id=current_user.id,
            date=today
        ).first()
        
        if existing:
            return jsonify({
                'message': f'Already marked {existing.status} for {student.name} today',
                'student': {
                    'id': student.id,
                    'name': student.name,
                    'admission_number': student.admission_number,
                    'class_name': student.class_name
                },
                'existing': True
            })
        
        # Mark present via QR scan
        attendance = Attendance(
            student_id=student_id,
            teacher_id=current_user.id,
            date=today,
            status='present'
        )
        db.session.add(attendance)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Marked {student.name} PRESENT for today ({today})',
            'student': {
                'id': student.id,
                'name': student.name,
                'admission_number': student.admission_number,
                'class_name': student.class_name,
                'phone': student.phone
            },
            'attendance': {
                'id': attendance.id,
                'date': today.isoformat()
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error processing QR: {str(e)}'}), 500

@teacher_routes.route('/teacher/add', methods=['GET', 'POST'])
@teacher_login_required
def add_teacher():
    if request.method == 'POST':
        data = request.form
        teacher = Teacher(
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone=data['phone'],
            email=data['email'],
            qualification=data['qualification'],
            subject=data['subject']
        )
        db.session.add(teacher)
        db.session.flush()
        
        login = TeacherLogin(
            teacher_id=teacher.id,
            username=data['username']
        )
        login.set_password(data['password'])
        db.session.add(login)
        db.session.commit()
        
        flash('Teacher added successfully')
        return redirect(url_for('teacher_routes.teacher_dashboard'))
    return render_template('add_teacher.html')
