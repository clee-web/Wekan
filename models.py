from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone, timedelta
from sqlalchemy import event, func, and_
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
db = SQLAlchemy()

class Student(db.Model):
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
    payments = db.relationship('Payment', back_populates='student', lazy=True, cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        super(Student, self).__init__(**kwargs)
        self.generate_admission_number()

    def generate_admission_number(self):
        if not self.admission_number:
            last_student = Student.query.order_by(Student.id.desc()).first()
            next_id = (last_student.id + 1) if last_student else 1
            self.admission_number = f'ADM-{next_id:04d}'

    def __repr__(self):
        return f'<Student {self.name} ({self.admission_number})>'

class Payment(db.Model):
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
    student = db.relationship('Student', back_populates='payments', lazy=True)

    def update_status(self):
        total_paid = sum(payment.amount for payment in self.student.payments if payment.payment_type == self.payment_type)
        total_required = self.total_fee
        if total_paid >= total_required:
            self.status = 'cleared'
        elif total_paid > 0:
            self.status = 'partial'
        else:
            self.status = 'pending'
        db.session.commit()

class ExamResult(db.Model):
    __tablename__ = 'exam_result'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    student = db.relationship('Student', backref='exam_results', lazy=True)
    exam_type = db.Column(db.String(50), nullable=False)
    marks_obtained = db.Column(db.Float, nullable=False)
    total_marks = db.Column(db.Float, nullable=False)
    grade = db.Column(db.String(2), nullable=False)
    remarks = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Teacher(db.Model):
    __tablename__ = 'teacher'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    class_name = db.Column(db.String(50))
    subject = db.Column(db.String(100))
    qualification = db.Column(db.String(100))
    avatar_url = db.Column(db.String(200))
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Teacher {self.first_name} {self.last_name}>'

    @property
    def name(self):
        return f"{self.first_name} {self.last_name}"

class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=True)
    teacher = db.relationship('Teacher', backref='attendances', lazy=True)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(10), nullable=False)
    session_type = db.Column(db.String(20), nullable=False, default='class')
    qr_token = db.Column(db.String(64), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Admin(UserMixin, db.Model):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def needs_password_reset(self):
        return self.password_hash and self.password_hash.startswith('scrypt:')

    def check_password(self, password):
        if self.needs_password_reset():
            return False
        try:
            return check_password_hash(self.password_hash, password)
        except ValueError:
            return False

class SubAdmin(UserMixin, db.Model):
    __tablename__ = 'sub_admin'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    email = db.Column(db.String(100), nullable=True)
    full_name = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=True)
    active = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        try:
            return check_password_hash(self.password_hash, password)
        except ValueError:
            return False

class TeacherLogin(UserMixin, db.Model):
    __tablename__ = 'teacher_login'
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    teacher = db.relationship('Teacher', backref='teacher_logins')
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    admin_set_timestamp = db.Column(db.DateTime, nullable=True)
    
    def set_password(self, password, admin_set=False):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        if admin_set:
            self.admin_set_timestamp = datetime.utcnow()
    
    def needs_password_reset(self):
        if self.password_hash and self.password_hash.startswith('scrypt:'):
            return True
        if self.admin_set_timestamp:
            return (datetime.utcnow() - self.admin_set_timestamp) > timedelta(days=30)
        return False

    def check_password(self, password):
        try:
            return check_password_hash(self.password_hash, password)
        except ValueError:
            return False

class Expenditure(db.Model):
    __tablename__ = 'expenditure'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    admin = db.relationship('Admin', backref='expenditures')
    
    def __repr__(self):
        return f'<Expenditure {self.description} KES{self.amount} on {self.date}>'

