"""
Script to sync existing SQLite data to Supabase
Run this after creating the Supabase tables
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from supabase_client import supabase
from datetime import datetime

# Initialize Flask app and database
app = Flask(__name__)
app.config.update(
    SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL', f'sqlite:///{os.path.join(os.path.dirname(__file__), "instance/academy.db")}'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
)

# Initialize db
db = SQLAlchemy()
db.init_app(app)

# Import models after db is initialized
from models import Student, Payment, ExamResult, Teacher, Attendance, Admin, TeacherLogin

def sync_students():
    """Sync students from SQLite to Supabase"""
    print("Syncing students...")
    students = Student.query.all()
    synced = 0
    errors = 0
    
    for student in students:
        try:
            data = {
                'admission_number': student.admission_number,
                'name': student.name,
                'phone': student.phone,
                'residence': student.residence,
                'class_name': student.class_name,
                'session': student.session,
                'next_of_kin_name': student.next_of_kin_name,
                'next_of_kin_relationship': student.next_of_kin_relationship,
                'next_of_kin_phone': student.next_of_kin_phone,
                'active': student.active,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            response = supabase.table('students').insert(data).execute()
            synced += 1
            print(f"  Synced: {student.name} ({student.admission_number})")
        except Exception as e:
            errors += 1
            print(f"  Error syncing {student.name}: {str(e)}")
    
    print(f"Students synced: {synced}, Errors: {errors}")
    return synced, errors

def sync_payments():
    """Sync payments from SQLite to Supabase"""
    print("Syncing payments...")
    payments = Payment.query.all()
    synced = 0
    errors = 0
    
    for payment in payments:
        try:
            # Get student UUID from Supabase by admission number
            student_response = supabase.table('students').select('id').eq('admission_number', payment.student.admission_number).execute()
            if not student_response.data:
                print(f"  Warning: Student not found for payment {payment.transaction_number}")
                errors += 1
                continue
            
            student_id = student_response.data[0]['id']
            
            data = {
                'student_id': student_id,
                'transaction_number': payment.transaction_number,
                'amount': payment.amount,
                'payment_type': payment.payment_type,
                'payment_method': payment.payment_method,
                'date': payment.date.isoformat() if payment.date else datetime.utcnow().isoformat(),
                'status': payment.status,
                'payment_category': payment.payment_category,
                'total_fee': payment.total_fee,
                'year': payment.year,
                'session': payment.session,
                'notes': payment.notes,
                'last_modified': payment.last_modified.isoformat() if payment.last_modified else datetime.utcnow().isoformat()
            }
            response = supabase.table('payments').insert(data).execute()
            synced += 1
            print(f"  Synced: Payment {payment.transaction_number}")
        except Exception as e:
            errors += 1
            print(f"  Error syncing payment {payment.transaction_number}: {str(e)}")
    
    print(f"Payments synced: {synced}, Errors: {errors}")
    return synced, errors

def sync_teachers():
    """Sync teachers from SQLite to Supabase"""
    print("Syncing teachers...")
    teachers = Teacher.query.all()
    synced = 0
    errors = 0
    
    for teacher in teachers:
        try:
            data = {
                'first_name': teacher.first_name,
                'last_name': teacher.last_name,
                'email': teacher.email,
                'phone': teacher.phone,
                'class_name': teacher.class_name,
                'subject': teacher.subject,
                'qualification': teacher.qualification,
                'avatar_url': teacher.avatar_url,
                'active': teacher.active,
                'created_at': teacher.created_at.isoformat() if teacher.created_at else datetime.utcnow().isoformat(),
                'updated_at': teacher.updated_at.isoformat() if teacher.updated_at else datetime.utcnow().isoformat()
            }
            response = supabase.table('teachers').insert(data).execute()
            synced += 1
            print(f"  Synced: {teacher.name}")
        except Exception as e:
            errors += 1
            print(f"  Error syncing {teacher.name}: {str(e)}")
    
    print(f"Teachers synced: {synced}, Errors: {errors}")
    return synced, errors

def sync_exam_results():
    """Sync exam results from SQLite to Supabase"""
    print("Syncing exam results...")
    exam_results = ExamResult.query.all()
    synced = 0
    errors = 0
    
    for exam_result in exam_results:
        try:
            # Get student UUID from Supabase by admission number
            student_response = supabase.table('students').select('id').eq('admission_number', exam_result.student.admission_number).execute()
            if not student_response.data:
                print(f"  Warning: Student not found for exam result")
                errors += 1
                continue
            
            student_id = student_response.data[0]['id']
            
            data = {
                'student_id': student_id,
                'exam_type': exam_result.exam_type,
                'marks_obtained': exam_result.marks_obtained,
                'total_marks': exam_result.total_marks,
                'grade': exam_result.grade,
                'remarks': exam_result.remarks,
                'created_at': exam_result.created_at.isoformat() if exam_result.created_at else datetime.utcnow().isoformat()
            }
            response = supabase.table('exam_results').insert(data).execute()
            synced += 1
            print(f"  Synced: Exam result for {exam_result.exam_type}")
        except Exception as e:
            errors += 1
            print(f"  Error syncing exam result: {str(e)}")
    
    print(f"Exam results synced: {synced}, Errors: {errors}")
    return synced, errors

def sync_attendance():
    """Sync attendance from SQLite to Supabase"""
    print("Syncing attendance...")
    attendance_records = Attendance.query.all()
    synced = 0
    errors = 0
    
    for attendance in attendance_records:
        try:
            # Get student UUID from Supabase by admission number
            student_response = supabase.table('students').select('id').eq('admission_number', attendance.student.admission_number).execute()
            if not student_response.data:
                print(f"  Warning: Student not found for attendance record")
                errors += 1
                continue
            
            student_id = student_response.data[0]['id']
            
            # Get teacher UUID if available
            teacher_id = None
            if attendance.teacher:
                teacher_response = supabase.table('teachers').select('id').eq('email', attendance.teacher.email).execute()
                if teacher_response.data:
                    teacher_id = teacher_response.data[0]['id']
            
            data = {
                'student_id': student_id,
                'teacher_id': teacher_id,
                'date': attendance.date.isoformat() if attendance.date else datetime.utcnow().isoformat(),
                'status': attendance.status,
                'session_type': attendance.session_type,
                'qr_token': attendance.qr_token,
                'created_at': attendance.created_at.isoformat() if attendance.created_at else datetime.utcnow().isoformat()
            }
            response = supabase.table('attendance').insert(data).execute()
            synced += 1
            print(f"  Synced: Attendance record")
        except Exception as e:
            errors += 1
            print(f"  Error syncing attendance: {str(e)}")
    
    print(f"Attendance synced: {synced}, Errors: {errors}")
    return synced, errors

def sync_admins():
    """Sync admins from SQLite to Supabase"""
    print("Syncing admins...")
    admins = Admin.query.all()
    synced = 0
    errors = 0
    
    for admin in admins:
        try:
            data = {
                'username': admin.username,
                'password_hash': admin.password_hash,
                'created_at': admin.created_at.isoformat() if admin.created_at else datetime.utcnow().isoformat()
            }
            response = supabase.table('admins').insert(data).execute()
            synced += 1
            print(f"  Synced: Admin {admin.username}")
        except Exception as e:
            errors += 1
            print(f"  Error syncing admin {admin.username}: {str(e)}")
    
    print(f"Admins synced: {synced}, Errors: {errors}")
    return synced, errors

def sync_teacher_logins():
    """Sync teacher logins from SQLite to Supabase"""
    print("Syncing teacher logins...")
    teacher_logins = TeacherLogin.query.all()
    synced = 0
    errors = 0
    
    for teacher_login in teacher_logins:
        try:
            # Get teacher UUID from Supabase by email
            teacher_response = supabase.table('teachers').select('id').eq('email', teacher_login.teacher.email).execute()
            if not teacher_response.data:
                print(f"  Warning: Teacher not found for teacher login")
                errors += 1
                continue
            
            teacher_id = teacher_response.data[0]['id']
            
            data = {
                'teacher_id': teacher_id,
                'username': teacher_login.username,
                'password_hash': teacher_login.password_hash,
                'created_at': datetime.utcnow().isoformat()
            }
            response = supabase.table('teacher_logins').insert(data).execute()
            synced += 1
            print(f"  Synced: Teacher login {teacher_login.username}")
        except Exception as e:
            errors += 1
            print(f"  Error syncing teacher login {teacher_login.username}: {str(e)}")
    
    print(f"Teacher logins synced: {synced}, Errors: {errors}")
    return synced, errors

def main():
    """Main sync function"""
    with app.app_context():
        print("Starting data sync to Supabase...")
        print("=" * 50)
        
        # Sync in order of dependencies
        sync_students()
        sync_teachers()
        sync_payments()
        sync_exam_results()
        sync_attendance()
        sync_admins()
        sync_teacher_logins()
        
        print("=" * 50)
        print("Data sync completed!")

if __name__ == '__main__':
    main()
