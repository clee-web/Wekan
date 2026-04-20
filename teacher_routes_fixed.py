from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_user, login_required, logout_user, current_user
from models import Teacher, TeacherLogin, Attendance, ExamResult, Student, db
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

teacher_routes = Blueprint('teacher_routes', __name__,
                          template_folder='../templates',
                          static_folder='../static')

@teacher_routes.route('/teacher/login', methods=['GET', 'POST'])
def teacher_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        print(f"Login attempt: username={username}")
        
        login = TeacherLogin.query.filter_by(username=username).first()
        if login:
            print(f"Found login record for username={username}")
        if login.check_password(password):
                print("Password check succeeded")
                login_user(login)
                print(f"Logged in user: {login.teacher.name}")
                return redirect(url_for('teacher_routes.teacher_dashboard'))
            else:
                print("Password check failed")
        else:
            print(f"No login record found for username={username}")
        flash('Invalid username or password')
    return render_template('teacher_login.html')

@teacher_routes.route('/teacher/logout')
@login_required
def teacher_logout():
    logout_user()
    return redirect(url_for('teacher_routes.teacher_login'))

@teacher_routes.route('/teacher/dashboard')
@login_required
def teacher_dashboard():
    classes = Student.query.filter_by(class_teacher_id=current_user.id).with_entities(Student.class_name).distinct().all()
    classes = [cls[0] for cls in classes]
    return render_template('teacher_dashboard.html', classes=classes)

@teacher_routes.route('/teacher/class/<class_name>')
@login_required
def class_students(class_name):
    students = Student.query.filter_by(
        class_name=class_name,
        class_teacher_id=current_user.id
    ).all()
    
    return render_template('class_students.html', 
                         class_name=class_name,
                         students=students)

@teacher_routes.route('/teacher/mark_attendance/<int:student_id>', methods=['POST'])
@login_required
def mark_attendance(student_id):
    student = Student.query.get_or_404(student_id)
    
    if student.class_teacher_id != current_user.id:
        flash('You cannot mark attendance for this student', 'error')
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
@login_required
def view_students():
    students = Student.query.filter_by(class_teacher_id=current_user.id).all()
    return render_template('view_students.html', students=students)

@teacher_routes.route('/teacher/mark_attendance', methods=['GET', 'POST'])
@login_required
def mark_attendance_bulk():
    if request.method == 'POST':
        data = request.json
        date = datetime.datetime.strptime(data['date'], '%Y-%m-%d').date()
        class_name = data.get('class_name')
        
        students = Student.query.filter_by(class_name=class_name, class_teacher_id=current_user.id).all()
        
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
    
    class_name = request.args.get('class_name')
    students = Student.query.filter_by(class_name=class_name, class_teacher_id=current_user.id).all()
    return render_template('mark_attendance.html', students=students)

@teacher_routes.route('/teacher/exam-results', methods=['GET', 'POST'])
@login_required
def manage_exam_results():
    if request.method == 'POST':
        data = request.json
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
    
    students = current_user.students
    return render_template('exam_results.html', students=students)

@teacher_routes.route('/teacher/add', methods=['GET', 'POST'])
@login_required
def add_teacher():
    if request.method == 'POST':
        data = request.form
        teacher = Teacher(
            name=data['name'],
            phone=data['phone'],
            email=data['email'],
            qualification=data['qualification'],
            subject=data['subject']
        )
        db.session.add(teacher)
        db.session.commit()
        
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
