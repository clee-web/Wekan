from datetime import date, datetime, timedelta
from models import db, Student, Attendance
from sqlalchemy import and_, func

def auto_mark_absent():
    """Auto-mark session 9 students absent after 5PM on Sat/Sun if no present record."""
    today = date.today()
    current_hour = datetime.now().hour
    
    # Only run after 17:00 on Saturday (5) or Sunday (6)
    if current_hour < 17 or today.weekday() not in [5, 6]:
        print(f"[{datetime.now()}] Auto-absent skipped: time={current_hour}, weekday={today.weekday()}")
        return
    
    print(f"[{datetime.now()}] Running auto-absent for {today}...")
    
    # Session 9 active students without 'present' record today (both class/leadership)
    session9_students = db.session.query(Student.id).filter(
        Student.session == '9',
        Student.active == True
    ).all()
    
    student_ids = [sid[0] for sid in session9_students]
    
    # Check for present in ANY session_type today
    present_students = db.session.query(Attendance.student_id.distinct()).filter(
        Attendance.student_id.in_(student_ids),
        Attendance.date == today,
        Attendance.status == 'present'
    ).all()
    
    present_ids = {pid[0] for pid in present_students}
    
    absent_needed = [sid for sid in student_ids if sid not in present_ids]
    
    # Mark absent if needed
    if absent_needed:
        absent_records = [Attendance(
            student_id=sid,
            date=today,
            status='absent',
            session_type='class' if today.weekday() == 5 else 'leadership'
        ) for sid in absent_needed]
        
        db.session.bulk_save_objects(absent_records)
        db.session.commit()
        print(f"Marked {len(absent_needed)} students absent.")
    
    # Check consecutive absents and deactivate if 3+
    from sqlalchemy import func
    recent_absents = db.session.query(
        Attendance.student_id,
        func.count(Attendance.id).label('absent_count')
    ).filter(
        Attendance.student_id.in_(db.session.query(Student.id).filter(Student.session == '9').subquery()),
        Attendance.status == 'absent',
        Attendance.date >= today - timedelta(days=21)  # Last 3 weeks
    ).group_by(Attendance.student_id).having(func.count(Attendance.id) >= 3).all()
    
    to_deactivate = []
    for student_id, _ in recent_absents:
        student = Student.query.filter_by(id=student_id, active=True).first()
        if student:
            student.active = False
            to_deactivate.append(student_id)
    
    if to_deactivate:
        db.session.commit()
        print(f"Deactivated {len(to_deactivate)} students (3+ absents in 3 weeks).")

