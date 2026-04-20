from flask import Blueprint, request, jsonify
from supabase_client import supabase
from datetime import datetime

supabase_bp = Blueprint('supabase_routes', __name__)

# Student Routes
@supabase_bp.route('/api/supabase/students', methods=['GET'])
def get_students():
    """Get all students from Supabase"""
    try:
        response = supabase.table('students').select('*').execute()
        return jsonify({'success': True, 'data': response.data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@supabase_bp.route('/api/supabase/students', methods=['POST'])
def create_student():
    """Create a new student in Supabase"""
    try:
        data = request.json
        response = supabase.table('students').insert(data).execute()
        return jsonify({'success': True, 'data': response.data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@supabase_bp.route('/api/supabase/students/<student_id>', methods=['GET'])
def get_student(student_id):
    """Get a specific student from Supabase"""
    try:
        response = supabase.table('students').select('*').eq('id', student_id).execute()
        if response.data:
            return jsonify({'success': True, 'data': response.data[0]})
        return jsonify({'success': False, 'error': 'Student not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@supabase_bp.route('/api/supabase/students/<student_id>', methods=['PUT'])
def update_student(student_id):
    """Update a student in Supabase"""
    try:
        data = request.json
        response = supabase.table('students').update(data).eq('id', student_id).execute()
        return jsonify({'success': True, 'data': response.data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@supabase_bp.route('/api/supabase/students/<student_id>', methods=['DELETE'])
def delete_student(student_id):
    """Delete a student from Supabase"""
    try:
        response = supabase.table('students').delete().eq('id', student_id).execute()
        return jsonify({'success': True, 'data': response.data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Payment Routes
@supabase_bp.route('/api/supabase/payments', methods=['GET'])
def get_payments():
    """Get all payments from Supabase"""
    try:
        response = supabase.table('payments').select('*').execute()
        return jsonify({'success': True, 'data': response.data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@supabase_bp.route('/api/supabase/payments', methods=['POST'])
def create_payment():
    """Create a new payment in Supabase"""
    try:
        data = request.json
        response = supabase.table('payments').insert(data).execute()
        return jsonify({'success': True, 'data': response.data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@supabase_bp.route('/api/supabase/payments/<payment_id>', methods=['PUT'])
def update_payment(payment_id):
    """Update a payment in Supabase"""
    try:
        data = request.json
        response = supabase.table('payments').update(data).eq('id', payment_id).execute()
        return jsonify({'success': True, 'data': response.data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Teacher Routes
@supabase_bp.route('/api/supabase/teachers', methods=['GET'])
def get_teachers():
    """Get all teachers from Supabase"""
    try:
        response = supabase.table('teachers').select('*').execute()
        return jsonify({'success': True, 'data': response.data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@supabase_bp.route('/api/supabase/teachers', methods=['POST'])
def create_teacher():
    """Create a new teacher in Supabase"""
    try:
        data = request.json
        response = supabase.table('teachers').insert(data).execute()
        return jsonify({'success': True, 'data': response.data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@supabase_bp.route('/api/supabase/teachers/<teacher_id>', methods=['PUT'])
def update_teacher(teacher_id):
    """Update a teacher in Supabase"""
    try:
        data = request.json
        response = supabase.table('teachers').update(data).eq('id', teacher_id).execute()
        return jsonify({'success': True, 'data': response.data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Attendance Routes
@supabase_bp.route('/api/supabase/attendance', methods=['GET'])
def get_attendance():
    """Get all attendance records from Supabase"""
    try:
        response = supabase.table('attendance').select('*').execute()
        return jsonify({'success': True, 'data': response.data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@supabase_bp.route('/api/supabase/attendance', methods=['POST'])
def create_attendance():
    """Create a new attendance record in Supabase"""
    try:
        data = request.json
        response = supabase.table('attendance').insert(data).execute()
        return jsonify({'success': True, 'data': response.data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@supabase_bp.route('/api/supabase/attendance/<attendance_id>', methods=['PUT'])
def update_attendance(attendance_id):
    """Update an attendance record in Supabase"""
    try:
        data = request.json
        response = supabase.table('attendance').update(data).eq('id', attendance_id).execute()
        return jsonify({'success': True, 'data': response.data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Exam Results Routes
@supabase_bp.route('/api/supabase/exam_results', methods=['GET'])
def get_exam_results():
    """Get all exam results from Supabase"""
    try:
        response = supabase.table('exam_results').select('*').execute()
        return jsonify({'success': True, 'data': response.data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@supabase_bp.route('/api/supabase/exam_results', methods=['POST'])
def create_exam_result():
    """Create a new exam result in Supabase"""
    try:
        data = request.json
        response = supabase.table('exam_results').insert(data).execute()
        return jsonify({'success': True, 'data': response.data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Real-time Subscription Route
@supabase_bp.route('/api/supabase/subscribe/<table_name>', methods=['POST'])
def subscribe_table(table_name):
    """Subscribe to real-time changes on a table"""
    try:
        # This would typically be handled via WebSocket on the client side
        # For now, we'll return configuration info
        return jsonify({
            'success': True,
            'message': f'Use Supabase client on frontend to subscribe to {table_name}',
            'table': table_name,
            'channel': f'{table_name}_changes'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
