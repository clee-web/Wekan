from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from models import db
from werkzeug.security import generate_password_hash

test_routes = Blueprint('test_routes', __name__,
                       template_folder='../templates',
                       static_folder='../static')

@test_routes.route('/test/dashboard')
def test_dashboard():
    return render_template('test/dashboard.html')

@test_routes.route('/test/students')
def test_students():
    return render_template('test/students.html')

@test_routes.route('/test/payments')
def test_payments():
    return render_template('test/payments.html')

@test_routes.route('/test/reports')
def test_reports():
    return render_template('test/reports.html')

@test_routes.route('/test/attendance')
def test_attendance():
    return render_template('test/attendance.html')

@test_routes.route('/test/exam-results')
def test_exam_results():
    return render_template('test/exam_results.html')

@test_routes.route('/test/settings')
def test_settings():
    return render_template('test/settings.html')

@test_routes.route('/test/api/students')
def test_api_students():
    students = [
        {
            'id': 1,
            'name': 'John Doe',
            'class': 'Form 4',
            'status': 'active'
        },
        {
            'id': 2,
            'name': 'Jane Smith',
            'class': 'Form 4',
            'status': 'active'
        }
    ]
    return jsonify(students)

@test_routes.route('/test/api/payments')
def test_api_payments():
    payments = [
        {
            'id': 1,
            'student_id': 1,
            'amount': 1000,
            'payment_type': 'graduation_fee',
            'status': 'pending'
        },
        {
            'id': 2,
            'student_id': 2,
            'amount': 500,
            'payment_type': 'passport_fee',
            'status': 'pending'
        }
    ]
    return jsonify(payments)

@test_routes.route('/test/api/reports')
def test_api_reports():
    report_data = {
        'total_students': 50,
        'total_payments': 100,
        'total_amount': 50000,
        'payment_types': {
            'graduation_fee': 30,
            'passport_fee': 20
        }
    }
    return jsonify(report_data)

@test_routes.route('/test/api/attendance')
def test_api_attendance():
    attendance = [
        {
            'id': 1,
            'student_id': 1,
            'date': '2023-09-01',
            'status': 'present'
        },
        {
            'id': 2,
            'student_id': 2,
            'date': '2023-09-01',
            'status': 'absent'
        }
    ]
    return jsonify(attendance)

@test_routes.route('/test/api/exam-results')
def test_api_exam_results():
    results = [
        {
            'id': 1,
            'student_id': 1,
            'subject': 'Mathematics',
            'marks': 75,
            'grade': 'A'
        },
        {
            'id': 2,
            'student_id': 2,
            'subject': 'English',
            'marks': 82,
            'grade': 'A+'
        }
    ]
    return jsonify(results)

@test_routes.route('/test/api/settings')
def test_api_settings():
    settings = {
        'school_name': 'Test School',
        'currency': 'KES',
        'graduation_fee': 1000,
        'passport_fee': 500
    }
    return jsonify(settings)
