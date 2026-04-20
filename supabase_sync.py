"""
Utility functions to automatically sync data to Supabase
Integrate this into routes to enable automatic syncing
"""
from supabase_client import supabase
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def sync_student_to_supabase(student):
    """Sync a single student to Supabase"""
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
            'active': bool(student.active),
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        # Check if student exists by admission_number
        existing = supabase.table('students').select('id').eq('admission_number', student.admission_number).execute()
        if existing.data:
            # Update existing student
            supabase.table('students').update(data).eq('admission_number', student.admission_number).execute()
            logger.info(f"Updated student in Supabase: {student.name} ({student.admission_number})")
        else:
            # Insert new student
            supabase.table('students').insert(data).execute()
            logger.info(f"Synced new student to Supabase: {student.name} ({student.admission_number})")
        return True
    except Exception as e:
        logger.error(f"Error syncing student {student.admission_number} to Supabase: {str(e)}")
        return False

def sync_payment_to_supabase(payment):
    """Sync a single payment to Supabase"""
    try:
        # Get student's admission_number
        from models import Student
        student = Student.query.get(payment.student_id)
        if not student or not student.admission_number:
            logger.warning(f"Cannot sync payment {payment.transaction_number}: student not found or missing admission_number")
            return False

        # Get student UUID from Supabase
        student_response = supabase.table('students').select('id').eq('admission_number', student.admission_number).execute()
        if not student_response.data:
            logger.warning(f"Cannot sync payment {payment.transaction_number}: student not found in Supabase")
            return False

        student_id_supabase = student_response.data[0]['id']

        data = {
            'student_id': student_id_supabase,
            'transaction_number': payment.transaction_number,
            'amount': payment.amount,
            'payment_type': payment.payment_type,
            'payment_method': payment.payment_method,
            'date': payment.date,
            'status': payment.status,
            'payment_category': payment.payment_category,
            'total_fee': payment.total_fee,
            'year': payment.year,
            'session': payment.session,
            'notes': payment.notes,
            'last_modified': payment.last_modified
        }

        # Check if payment exists by transaction_number
        existing = supabase.table('payments').select('id').eq('transaction_number', payment.transaction_number).execute()
        if existing.data:
            # Update existing payment
            supabase.table('payments').update(data).eq('transaction_number', payment.transaction_number).execute()
            logger.info(f"Updated payment in Supabase: {payment.transaction_number}")
        else:
            # Insert new payment
            supabase.table('payments').insert(data).execute()
            logger.info(f"Synced new payment to Supabase: {payment.transaction_number}")
        return True
    except Exception as e:
        logger.error(f"Error syncing payment {payment.transaction_number} to Supabase: {str(e)}")
        return False

def sync_teacher_to_supabase(teacher):
    """Sync a single teacher to Supabase"""
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
            'active': bool(teacher.active),
            'created_at': teacher.created_at if teacher.created_at else datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        # Check if teacher exists by email
        existing = supabase.table('teachers').select('id').eq('email', teacher.email).execute()
        if existing.data:
            # Update existing teacher
            supabase.table('teachers').update(data).eq('email', teacher.email).execute()
            logger.info(f"Updated teacher in Supabase: {teacher.first_name} {teacher.last_name}")
        else:
            # Insert new teacher
            supabase.table('teachers').insert(data).execute()
            logger.info(f"Synced new teacher to Supabase: {teacher.first_name} {teacher.last_name}")
        return True
    except Exception as e:
        logger.error(f"Error syncing teacher {teacher.email} to Supabase: {str(e)}")
        return False

def sync_admin_to_supabase(admin):
    """Sync a single admin to Supabase"""
    try:
        data = {
            'username': admin.username,
            'password_hash': admin.password_hash,
            'email': admin.email,
            'created_at': admin.created_at if admin.created_at else datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        # Check if admin exists by username
        existing = supabase.table('admins').select('id').eq('username', admin.username).execute()
        if existing.data:
            # Update existing admin
            supabase.table('admins').update(data).eq('username', admin.username).execute()
            logger.info(f"Updated admin in Supabase: {admin.username}")
        else:
            # Insert new admin
            supabase.table('admins').insert(data).execute()
            logger.info(f"Synced new admin to Supabase: {admin.username}")
        return True
    except Exception as e:
        logger.error(f"Error syncing admin {admin.username} to Supabase: {str(e)}")
        return False

def sync_teacher_login_to_supabase(teacher_login):
    """Sync a single teacher login to Supabase"""
    try:
        from models import Teacher
        teacher = Teacher.query.get(teacher_login.teacher_id)
        if not teacher or not teacher.email:
            logger.warning(f"Cannot sync teacher login: teacher not found or missing email")
            return False

        # Get teacher UUID from Supabase
        teacher_response = supabase.table('teachers').select('id').eq('email', teacher.email).execute()
        if not teacher_response.data:
            logger.warning(f"Cannot sync teacher login: teacher not found in Supabase")
            return False

        teacher_id_supabase = teacher_response.data[0]['id']

        data = {
            'teacher_id': teacher_id_supabase,
            'username': teacher_login.username,
            'password_hash': teacher_login.password_hash,
            'created_at': teacher_login.created_at if teacher_login.created_at else datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }

        # Check if teacher_login exists by username
        existing = supabase.table('teacher_logins').select('id').eq('username', teacher_login.username).execute()
        if existing.data:
            # Update existing teacher_login
            supabase.table('teacher_logins').update(data).eq('username', teacher_login.username).execute()
            logger.info(f"Updated teacher login in Supabase: {teacher_login.username}")
        else:
            # Insert new teacher_login
            supabase.table('teacher_logins').insert(data).execute()
            logger.info(f"Synced new teacher login to Supabase: {teacher_login.username}")
        return True
    except Exception as e:
        logger.error(f"Error syncing teacher login {teacher_login.username} to Supabase: {str(e)}")
        return False
