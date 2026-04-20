"""
Simple script to sync SQLite data to Supabase using direct SQLite access
Run this after creating the Supabase tables
"""
import sqlite3
import json
from supabase_client import supabase
from datetime import datetime

# SQLite database path
DB_PATH = 'instance/academy.db'

def get_students():
    """Get all students from SQLite"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM student")
    columns = [description[0] for description in cursor.description]
    students = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    return students

def get_payments():
    """Get all payments from SQLite"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM payment")
    columns = [description[0] for description in cursor.description]
    payments = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    return payments

def get_teachers():
    """Get all teachers from SQLite"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM teacher")
    columns = [description[0] for description in cursor.description]
    teachers = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    return teachers

def get_exam_results():
    """Get all exam results from SQLite"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM exam_result")
    columns = [description[0] for description in cursor.description]
    exam_results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    return exam_results

def get_attendance():
    """Get all attendance records from SQLite"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM attendance")
    columns = [description[0] for description in cursor.description]
    attendance = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    return attendance

def get_admins():
    """Get all admins from SQLite"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM admin")
    columns = [description[0] for description in cursor.description]
    admins = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    return admins

def get_teacher_logins():
    """Get all teacher logins from SQLite"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM teacher_login")
    columns = [description[0] for description in cursor.description]
    teacher_logins = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    return teacher_logins

def sync_students():
    """Sync students to Supabase"""
    print("Syncing students...")
    students = get_students()
    synced = 0
    errors = 0
    
    for student in students:
        try:
            data = {
                'admission_number': student['admission_number'],
                'name': student['name'],
                'phone': student['phone'],
                'residence': student['residence'],
                'class_name': student['class_name'],
                'session': student['session'],
                'next_of_kin_name': student['next_of_kin_name'],
                'next_of_kin_relationship': student['next_of_kin_relationship'],
                'next_of_kin_phone': student['next_of_kin_phone'],
                'active': bool(student['active']),
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            response = supabase.table('students').insert(data)
            synced += 1
            print(f"  Synced: {student['name']} ({student['admission_number']})")
        except Exception as e:
            errors += 1
            print(f"  Error syncing {student['name']}: {str(e)}")
            if errors <= 3:  # Show full error for first 3 errors
                import traceback
                traceback.print_exc()
    
    print(f"Students synced: {synced}, Errors: {errors}")
    return synced, errors

def sync_payments():
    """Sync payments to Supabase"""
    print("Syncing payments...")
    payments = get_payments()
    synced = 0
    errors = 0
    
    # Build a mapping of student_id to admission_number from SQLite
    students = get_students()
    student_map = {s['id']: s['admission_number'] for s in students if s.get('admission_number')}
    
    for payment in payments:
        try:
            # Get student_id from payment
            student_id_sqlite = payment.get('student_id')
            if not student_id_sqlite:
                print(f"  Warning: Missing student_id for payment {payment.get('transaction_number', 'UNKNOWN')}")
                errors += 1
                continue
            
            # Get admission_number from student map
            admission_number = student_map.get(student_id_sqlite)
            if not admission_number:
                print(f"  Warning: Student {student_id_sqlite} not found or missing admission_number (payment {payment.get('transaction_number', 'UNKNOWN')})")
                errors += 1
                continue
            
            # Get student UUID from Supabase by admission number
            student_response = supabase.table('students').select('id').eq('admission_number', admission_number).execute()
            if not student_response.data:
                print(f"  Warning: Student not found in Supabase for admission_number {admission_number} (payment {payment['transaction_number']})")
                errors += 1
                continue
            
            student_id_supabase = student_response.data[0]['id']
            
            data = {
                'student_id': student_id_supabase,
                'transaction_number': payment['transaction_number'],
                'amount': payment['amount'],
                'payment_type': payment['payment_type'],
                'payment_method': payment['payment_method'],
                'date': payment['date'],
                'status': payment['status'],
                'payment_category': payment['payment_category'],
                'total_fee': payment['total_fee'],
                'year': payment['year'],
                'session': payment['session'],
                'notes': payment['notes'],
                'last_modified': payment['last_modified']
            }
            response = supabase.table('payments').insert(data)
            synced += 1
            print(f"  Synced: Payment {payment['transaction_number']}")
        except Exception as e:
            errors += 1
            print(f"  Error syncing payment {payment.get('transaction_number', 'UNKNOWN')}: {str(e)}")
            if errors <= 3:
                import traceback
                traceback.print_exc()
    
    print(f"Payments synced: {synced}, Errors: {errors}")
    return synced, errors

def sync_teachers():
    """Sync teachers to Supabase"""
    print("Syncing teachers...")
    teachers = get_teachers()
    synced = 0
    errors = 0

    for teacher in teachers:
        try:
            data = {
                'first_name': teacher['first_name'],
                'last_name': teacher['last_name'],
                'email': teacher['email'],
                'phone': teacher['phone'],
                'class_name': teacher['class_name'],
                'subject': teacher['subject'],
                'qualification': teacher['qualification'],
                'avatar_url': teacher['avatar_url'],
                'active': bool(teacher['active']),
                'created_at': teacher['created_at'],
                'updated_at': teacher['updated_at']
            }
            response = supabase.table('teachers').insert(data)
            synced += 1
            print(f"  Synced: {teacher['first_name']} {teacher['last_name']}")
        except Exception as e:
            errors += 1
            print(f"  Error syncing {teacher['first_name']} {teacher['last_name']}: {str(e)}")

    print(f"Teachers synced: {synced}, Errors: {errors}")
    return synced, errors

def sync_admins():
    """Sync admins to Supabase"""
    print("Syncing admins...")
    admins = get_admins()
    synced = 0
    errors = 0

    for admin in admins:
        try:
            data = {
                'username': admin['username'],
                'password_hash': admin['password_hash'],
                'email': admin.get('email'),
                'created_at': admin.get('created_at', datetime.utcnow().isoformat()),
                'updated_at': admin.get('updated_at', datetime.utcnow().isoformat())
            }
            response = supabase.table('admins').insert(data)
            synced += 1
            print(f"  Synced: {admin['username']}")
        except Exception as e:
            errors += 1
            print(f"  Error syncing {admin['username']}: {str(e)}")

    print(f"Admins synced: {synced}, Errors: {errors}")
    return synced, errors

def sync_teacher_logins():
    """Sync teacher logins to Supabase"""
    print("Syncing teacher logins...")
    teacher_logins = get_teacher_logins()
    synced = 0
    errors = 0

    # Build a mapping of teacher_id to email from SQLite
    teachers = get_teachers()
    teacher_map = {t['id']: t['email'] for t in teachers if t.get('email')}

    for teacher_login in teacher_logins:
        try:
            # Get teacher_id from teacher_login
            teacher_id_sqlite = teacher_login.get('teacher_id')
            if not teacher_id_sqlite:
                print(f"  Warning: Missing teacher_id for teacher_login")
                errors += 1
                continue

            # Get teacher email from teacher map
            teacher_email = teacher_map.get(teacher_id_sqlite)
            if not teacher_email:
                print(f"  Warning: Teacher {teacher_id_sqlite} not found or missing email")
                errors += 1
                continue

            # Get teacher UUID from Supabase by email
            teacher_response = supabase.table('teachers').select('id').eq('email', teacher_email).execute()
            if not teacher_response.data:
                print(f"  Warning: Teacher not found in Supabase for email {teacher_email}")
                errors += 1
                continue

            teacher_id_supabase = teacher_response.data[0]['id']

            data = {
                'teacher_id': teacher_id_supabase,
                'username': teacher_login['username'],
                'password_hash': teacher_login['password_hash'],
                'created_at': teacher_login.get('created_at', datetime.utcnow().isoformat()),
                'updated_at': teacher_login.get('updated_at', datetime.utcnow().isoformat())
            }
            response = supabase.table('teacher_logins').insert(data)
            synced += 1
            print(f"  Synced: {teacher_login['username']}")
        except Exception as e:
            errors += 1
            print(f"  Error syncing {teacher_login.get('username', 'UNKNOWN')}: {str(e)}")

    print(f"Teacher logins synced: {synced}, Errors: {errors}")
    return synced, errors

def main():
    """Main sync function"""
    print("Starting data sync to Supabase...")
    print("=" * 50)

    # Sync in order of dependencies
    sync_students()
    sync_teachers()
    sync_payments()
    sync_admins()
    sync_teacher_logins()

    print("=" * 50)
    print("Data sync completed!")

if __name__ == '__main__':
    main()
