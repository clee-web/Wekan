from flask import Flask
from models import Student, db

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/academy.db'
db.init_app(app)

with app.app_context():
    student = Student.query.filter_by(name='ANDREW CHARLES OKOTH').first()
    if student:
        print(f'Student ID: {student.id}, Session: {student.session}, Active: {student.active}')
    else:
        print('Student not found')
