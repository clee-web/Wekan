from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from models import db, Student, Attendance
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_
import uuid
import re

qr_routes = Blueprint('qr_routes', __name__, template_folder='../templates', static_folder='../static')

@qr_routes.route('/qr_attendance')
def qr_attendance_page():
    """QR Scanner page - public access for students to scan"""
    students = Student.query.filter_by(active=True).limit(10).all()  # Sample for testing
    return render_template('qr_attendance.html', students=students)

@qr_routes.route('/scan_qr', methods=['POST'])
def scan_qr():
    """Process QR scan - extract student ID, mark attendance, check leadership absences"""
    try:
        data = request.json.get('qr_data')
        if not data:
            print(f"DEBUG: No QR data provided. Request JSON: {request.json}")
            return jsonify({'error': 'No QR data provided'}), 400
        
        print(f"DEBUG: QR data received: {data}")
        
        # Parse QR data: 'IYF-Student:{id}-{name}'
        match = re.match(r'IYF-Student:(\d+)-(.+)', data.strip())
        if not match:
            print(f"DEBUG: QR format mismatch. Expected: IYF-Student:{{id}}-{{name}}, Got: {data}")
            return jsonify({'error': 'Invalid QR format'}), 400
        
        student_id = int(match.group(1))
        scanned_name = match.group(2)
        
        # Lookup student
        student = Student.query.get(student_id)
        if not student:
            return jsonify({'error': 'Student not found'}), 404
        
        if scanned_name != student.name:
            return jsonify({'error': 'Name mismatch - possible fake QR'}), 403
        
        today = date.today()
        weekday = today.weekday()  # 5=Sat, 6=Sun
        
        # Determine session_type: Sat=class, Sun=class or leadership (default class for now, can add time param)
        if weekday == 5:  # Saturday
            session_type = 'class'
        elif weekday == 6:  # Sunday
            session_type = request.json.get('session_type', 'class')  # Frontend can specify 'leadership'
            if session_type not in ['class', 'leadership']:
                session_type = 'class'
        else:
            return jsonify({'error': 'QR attendance only on Sat/Sun'}), 400
        
        # Check if already marked today for this session_type
        existing = Attendance.query.filter(
            and_(
                Attendance.student_id == student_id,
                Attendance.date == today,
                Attendance.session_type == session_type
            )
        ).first()
        
        if existing:
            return jsonify({
                'message': f'Already marked {existing.status} for {session_type} today',
                'student': {'id': student.id, 'name': student.name, 'active': student.active}
            })
        
        # Mark present via QR scan
        attendance = Attendance(
            student_id=student_id,
            teacher_id=None,  # QR self-scan, no teacher
            date=today,
            status='present',
            session_type=session_type,
            qr_token=str(uuid.uuid4().hex)[:32]
        )
        db.session.add(attendance)
        db.session.flush()  # Get ID
        
        # If leadership and was absent before? No, QR=always present. But check post-mark for logic
        if session_type == 'leadership':
            check_leadership_deactivation(student_id)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Marked {student.name} PRESENT for {session_type.upper()} ({today})',
            'student': {
                'id': student.id,
                'name': student.name,
                'admission_number': student.admission_number,
                'class_name': student.class_name,
                'active': student.active
            },
            'attendance': {
                'id': attendance.id,
                'qr_token': attendance.qr_token,
                'date': today.isoformat()
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

def check_leadership_deactivation(student_id):
    """Check if student has 3+ leadership absences → deactivate"""
    today = date.today()
    
    # Count leadership absences for student (last 4 weeks or configurable)
    absence_count = db.session.query(func.count(Attendance.id)).filter(
        and_(
            Attendance.student_id == student_id,
            Attendance.session_type == 'leadership',
            Attendance.status == 'absent',
            Attendance.date >= today - timedelta(weeks=4)  # Recent 4 Sundays
        )
    ).scalar()
    
    if absence_count >= 3:
        student = Student.query.get(student_id)
        if student.active:
            student.active = False
            db.session.commit()
            print(f"AUTO-DEACTIVATED student {student_id} - {absence_count} leadership absences")
    
    return absence_count

@qr_routes.route('/api/leadership_status/<int:student_id>')
def leadership_status(student_id):
    """Get leadership absence count for student"""
    student = Student.query.get_or_404(student_id)
    count = db.session.query(func.count(Attendance.id)).filter(
        and_(
            Attendance.student_id == student_id,
            Attendance.session_type == 'leadership',
            Attendance.status == 'absent'
        )
    ).scalar()
    return jsonify({'absences': count, 'active': student.active})

# Admin-only reactivation (add auth later)
@qr_routes.route('/admin/activate/<int:student_id>', methods=['POST'])
def admin_activate(student_id):
    student = Student.query.get_or_404(student_id)
    student.active = True
    db.session.commit()
    return jsonify({'success': True, 'message': f'{student.name} reactivated'})
