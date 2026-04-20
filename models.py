from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from sqlalchemy import event, func
db = SQLAlchemy()

class Student(db.Model):
    """Model representing a student."""
    __tablename__ = 'student'
    
    id = db.Column(db.Integer, primary_key=True)
    admission_number = db.Column(db.String(20), unique=True, nullable=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    residence = db.Column(db.String(100), nullable=False)
    class_name = db.Column(db.String(50), nullable=False)
    session = db.Column(db.String(50), nullable=False)
    next_of_kin_name = db.Column(db.String(100), nullable=False, default='')
    next_of_kin_relationship = db.Column(db.String(50), nullable=False, default='')
    next_of_kin_phone = db.Column(db.String(20), nullable=False, default='')
    active = db.Column(db.Boolean, nullable=False, default=True)
    
    # Relationship to payments
    payments = db.relationship('Payment', back_populates='student', lazy=True, cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        super(Student, self).__init__(**kwargs)
        self.generate_admission_number()

    def generate_admission_number(self):
        """Generate a new admission number if one doesn't exist"""
        if not self.admission_number:
            # Get the last student's ID and increment by 1
            last_student = Student.query.order_by(Student.id.desc()).first()
            next_id = (last_student.id + 1) if last_student else 1
            self.admission_number = f'ADM-{next_id:04d}'

    def __repr__(self):
        return f'<Student {self.name} ({self.admission_number})>'

class Payment(db.Model):
    """Model representing a payment transaction."""
    __tablename__ = 'payment'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    transaction_number = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_type = db.Column(db.String(50), nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    status = db.Column(db.String(20), nullable=False, default='pending')
    payment_category = db.Column(db.String(50), nullable=False, default='school_fee')
    total_fee = db.Column(db.Float, nullable=False, default=1500.0)
    year = db.Column(db.String(10), nullable=False)
    session = db.Column(db.String(50), nullable=False)
    notes = db.Column(db.Text)
    last_modified = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationship to student
    student = db.relationship('Student', back_populates='payments', lazy=True)
    
    def update_status(self):
        """Update payment status based on total amount paid."""
        # Get total paid amount for this payment type
        total_paid = sum(payment.amount for payment in self.student.payments 
                         if payment.payment_type == self.payment_type)
        
        # Get total required fee for this payment type
        total_required = self.total_fee
        
        # Update status based on total paid amount for this payment type
        if total_paid >= total_required:
            self.status = 'cleared'
        elif total_paid > 0:
            self.status = 'partial'
        else:
            self.status = 'pending'
        
        db.session.commit()

    @classmethod
    def find_duplicates(cls, student_id=None):
        """Find duplicate payment groups (same date/type/method/amount/status)."""
        query = db.session.query(
            cls.student_id,
            func.date(cls.date).label('payment_date'),
            cls.payment_type,
            cls.payment_method,
            cls.amount,
            cls.status,
            func.count(cls.id).label('count'),
            func.min(cls.id).label('min_id'),
            func.max(cls.id).label('max_id')
        ).group_by(
            cls.student_id,
            func.date(cls.date),
            cls.payment_type,
            cls.payment_method,
            cls.amount,
            cls.status
        ).having(func.count(cls.id) > 1)

        if student_id:
            query = query.filter(cls.student_id == student_id)

        return query.all()

    @classmethod
    def remove_duplicates(cls, student_id=None, dry_run=True):
        """Remove duplicates for student or all, keep newest (max ID). Returns count removed."""
        duplicates = cls.find_duplicates(student_id)
        total_removed = 0
        
        for group in duplicates:
            s_id, p_date, p_type, p_method, amt, stat, cnt, minid, maxid = group
            
            if dry_run:
                print(f"DRY-RUN: Keep ID {maxid}, delete {cnt-1} duplicates for student {s_id} on {p_date} ({p_type}, KSh{amt:.2f})")
            else:
                deleted = db.session.query(cls).filter(
                    and_(
                        cls.student_id == s_id,
                        func.date(cls.date) == p_date,
                        cls.payment_type == p_type,
                        cls.payment_method == p_method,
                        cls.amount == amt,
                        cls.status == stat,
                        cls.id < maxid
                    )
                ).delete(synchronize_session=False)
                total_removed += deleted
        
        if not dry_run:
            db.session.commit()
        
        return total_removed

    @staticmethod
    def initiate_mpesa_payment(student_id, amount):
        """Initiate M-PESA STK push payment."""
        from mpesa_integration import mpesa
        
        # Get student details
        student = Student.query.get(student_id)
        if not student:
            return False, "Student not found"

        # Generate unique reference
        reference = f"PAY{student_id}{datetime.now().strftime('%Y%m%d%H%S')}"

        # Initiate STK push
        success, response = mpesa.stk_push(
            phone_number=student.phone,
            amount=amount,
            account_reference=reference,
            transaction_desc=f"Payment for {student.name}"
        )

        if success:
            # Create pending payment record
            payment = Payment(
                student_id=student_id,
                transaction_number=reference,
                amount=amount,
                payment_type='mpesa',
                payment_method='mpesa',
                status='pending',
                year=datetime.now().strftime('%Y'),
                session='current',
            )
            db.session.add(payment)
            db.session.commit()
            return True, payment
        
        return False, response

class ExamResult(db.Model):
    """Model representing an exam result."""
    __tablename__ = 'exam_result'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    student = db.relationship('Student', backref='exam_results', lazy=True, foreign_keys=[student_id])
    exam_type = db.Column(db.String(50), nullable=False)
    marks_obtained = db.Column(db.Float, nullable=False)
    total_marks = db.Column(db.Float, nullable=False)
    grade = db.Column(db.String(2), nullable=False)
    remarks = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = {
        'sqlite_autoincrement': True
    }

class Teacher(db.Model):
    """Model representing a teacher."""
    __tablename__ = 'teacher'
    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    class_name = db.Column(db.String(50))  # Optional, if teacher is assigned to a specific class
    subject = db.Column(db.String(100))  # Subject taught by the teacher
    qualification = db.Column(db.String(100))  # Teacher's qualification
    avatar_url = db.Column(db.String(200))  # URL to teacher's avatar/photo
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Teacher {self.first_name} {self.last_name}>'

    @property
    def name(self):
        """Full name of the teacher."""
        return f"{self.first_name} {self.last_name}"

class Attendance(db.Model):
    """Model representing student attendance with QR and leadership support."""
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=True)
    teacher = db.relationship('Teacher', backref='attendances', lazy=True)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(10), nullable=False)  # 'present' or 'absent'
    session_type = db.Column(db.String(20), nullable=False, default='class')  # 'class' or 'leadership'
    qr_token = db.Column(db.String(64), unique=True, nullable=True)  # Unique token for QR scan verification
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Attendance {self.student_id} - {self.date} ({self.status}, {self.session_type})>'

# Admin model for admin authentication
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
class Admin(UserMixin, db.Model):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        try:
            return check_password_hash(self.password_hash, password)
        except ValueError:
            # Hash method not supported (e.g., scrypt), password needs reset
            return False


class TeacherLogin(UserMixin, db.Model):
    __tablename__ = 'teacher_login'
    
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    teacher = db.relationship('Teacher', backref='teacher_logins')
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        try:
            return check_password_hash(self.password_hash, password)
        except ValueError:
            # Hash method not supported (e.g., scrypt), password needs reset
            return False
