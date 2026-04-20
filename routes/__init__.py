from flask import Blueprint, render_template, jsonify, request, Response
from flask_login import login_required, current_user
from models import Student, Payment, Teacher, db
from sqlalchemy import func
import io
from fpdf import FPDF
from datetime import datetime
import xlsxwriter # Already in your requirements.txt

# Define the Blueprint.
# The 'template_folder' and 'static_folder' paths are relative to the Blueprint's location.
# If 'routes' is a package (e.g., e:\payments\routes\), and 'templates' is e:\payments\templates\,
# then '../templates' is correct.
main_routes = Blueprint(
    'main_routes',
    __name__,
    template_folder='../templates',
    static_folder='../static'
)

# --- Database Interactions (Replaces Mock Data) ---
# This data is for demonstration. You'll need to query your database.
# MOCK_CLASSES_DB is no longer needed as we query the database.

# MOCK_STUDENTS_DB is no longer needed.
# GRADUATION_FEE_PAYMENT_TYPE = 'graduation_fee' # Define your specific payment type for graduation fees
# Make sure this matches what's stored in your Payment.payment_type column for graduation fees.



GRADUATION_FEE_TOTAL = 1000.00 # KES 1000 as per requirements

# --- Routes ---

@main_routes.route('/teachers', endpoint='teachers')
@login_required
def teachers():
    """Serves the teachers management page."""
    return render_template('teachers.html')

@main_routes.route('/api/teachers', methods=['GET'])
@login_required
def get_teachers():
    """API endpoint to get all teachers."""
    try:
        teachers = db.session.query(Teacher).all()
        return jsonify([{
            'id': teacher.id,
            'name': f"{teacher.first_name} {teacher.last_name}",
            'email': teacher.email,
            'phone': teacher.phone,
            'class_name': teacher.class_name
        } for teacher in teachers])
    except Exception as e:
        print(f"Error fetching teachers: {e}")
        return jsonify({'error': 'Could not fetch teachers from database'}), 500

@main_routes.route('/api/teachers', methods=['POST'])
@login_required
def add_teacher():
    """API endpoint to add a new teacher."""
    try:
        data = request.get_json()
        teacher = Teacher(
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            phone=data['phone'],
            class_name=data.get('class_name')
        )
        db.session.add(teacher)
        db.session.commit()
        return jsonify({'message': 'Teacher added successfully'}), 201
    except Exception as e:
        print(f"Error adding teacher: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to add teacher'}), 500

@main_routes.route('/api/teachers/<int:teacher_id>', methods=['PUT'])
@login_required
def update_teacher(teacher_id):
    """API endpoint to update a teacher's information."""
    try:
        teacher = db.session.query(Teacher).get_or_404(teacher_id)
        data = request.get_json()
        teacher.first_name = data['first_name']
        teacher.last_name = data['last_name']
        teacher.email = data['email']
        teacher.phone = data['phone']
        teacher.class_name = data.get('class_name')
        db.session.commit()
        return jsonify({'message': 'Teacher updated successfully'})
    except Exception as e:
        print(f"Error updating teacher: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update teacher'}), 500

@main_routes.route('/api/teachers/<int:teacher_id>', methods=['DELETE'])
@login_required
def delete_teacher(teacher_id):
    """API endpoint to delete a teacher."""
    try:
        teacher = db.session.query(Teacher).get_or_404(teacher_id)
        db.session.delete(teacher)
        db.session.commit()
        return jsonify({'message': 'Teacher deleted successfully'})
    except Exception as e:
        print(f"Error deleting teacher: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to delete teacher'}), 500

@main_routes.route('/student-payment-status')
def student_payment_status_page():
    """Serves the student payment status HTML page."""
    return render_template('student_payment_status.html')

@main_routes.route('/api/classes', methods=['GET'])
def get_classes_api():
    """API endpoint to get the list of available classes with normalization."""
    try:
        # Get all class names from the database
        classes_from_db = db.session.query(Student.class_name).filter(Student.class_name.isnot(None)).all()
        
        # Use a set to store unique normalized class names
        unique_classes = set()
        
        for c_tuple in classes_from_db:
            original_name = c_tuple[0]
            if original_name:  # Ensure not None or empty string
                normalized_name = original_name.strip().upper()
                if normalized_name:
                    unique_classes.add(normalized_name)
        
        # Convert the set to a sorted list of dictionaries
        # Add 'All Classes' option at the top
        classes_data = [{'id': '', 'name': 'All Classes'}]
        classes_data.extend([{'id': class_name, 'name': class_name} 
                           for class_name in sorted(unique_classes)])
        
        return jsonify(classes_data)
    except Exception as e:
        print(f"Error fetching classes: {e}")
        return jsonify({'error': 'Could not fetch classes from database'}), 500


@main_routes.route('/api/sessions', methods=['GET'])
def get_sessions_api():
    """API endpoint to get the list of available sessions."""
    try:
        # Get all distinct sessions and order them
        sessions_from_db = db.session.query(Student.session)\
            .filter(Student.session.isnot(None))\
            .distinct()\
            .order_by(Student.session)\
            .all()
        
        # Extract numeric values from session strings (assuming format like "Session 1", "Session 2", etc.)
        session_numbers = []
        for session in sessions_from_db:
            try:
                # Extract number from string (e.g., "Session 1" -> 1)
                number = int(''.join(filter(str.isdigit, session[0])))
                session_numbers.append(number)
            except (ValueError, TypeError):
                continue
        
        # Get the maximum session number
        if not session_numbers:
            return jsonify([])
        
        max_session = max(session_numbers)
        
        # Generate sequential session numbers starting from 1
        sessions_data = [{'id': i, 'name': f'Session {i}'} for i in range(1, max_session + 1)]
        
        return jsonify(sessions_data)
    except Exception as e:
        print(f"Error fetching sessions: {e}")
        return jsonify({'error': 'Could not fetch sessions from database'}), 500

@main_routes.route('/api/students', methods=['GET'])
def get_students_api():
    """API endpoint to get students for a selected class and session, and their graduation fee status."""
    class_id = request.args.get('classId')
    session_id_str = request.args.get('sessionId')

    GRADUATION_FEE_PAYMENT_TYPE = 'Graduation Fee'

    try:
        # If class_id is empty, return all students
        if not class_id:
            students = Student.query.all()
        else:
            # Get all students for the given class
            students = Student.query.filter(Student.class_name == class_id).all()
        
        if not students:
            return jsonify([])

        students_data = []
        for student in students:
            # Get total paid for graduation fee
            grad_payment_total = db.session.query(func.sum(Payment.amount)) \
                               .filter(Payment.student_id == student.id, 
                                       Payment.payment_type == GRADUATION_FEE_PAYMENT_TYPE).scalar() or 0.0
            
            # Check if session matches if specified
            if session_id_str and session_id_str.isdigit():
                # Extract session number from session string
                current_session_number = int(''.join(filter(str.isdigit, student.session)))
                if current_session_number != int(session_id_str):
                    continue
            
            students_data.append({
                'id': student.id,
                'name': student.name,
                'graduation_fee_paid': float(grad_payment_total)
            })
        
        return jsonify(students_data)
    except Exception as e:
        print(f"Error fetching students for class {class_id} and session {session_id_str}: {e}")
        return jsonify({'error': f'Could not fetch students for class {class_id} from database'}), 500

def _get_filtered_report_data(class_id, status_filter, session_id_str=None):
    GRADUATION_FEE_PAYMENT_TYPE = 'Graduation Fee'
    """Helper to fetch and filter student data for reports based on graduation fee, class, and session."""
    try:
        # If class_id is empty, get all students ("All Classes" case)
        if not class_id:
            query = Student.query
        else:
            # class_id is expected to be the normalized class_name string
            query = Student.query.filter(func.upper(func.trim(Student.class_name)) == class_id)

        if session_id_str and session_id_str.isdigit():
            # Extract session number from session string
            query = query.filter(Student.session.like(f'%{session_id_str}%'))
        
        students_in_query = query.all()

        report_data = []
        for student_db_obj in students_in_query:
            paid_amount = db.session.query(func.sum(Payment.amount)) \
                               .filter(Payment.student_id == student_db_obj.id, 
                                       Payment.payment_type == GRADUATION_FEE_PAYMENT_TYPE).scalar() or 0.0
            paid_amount = float(paid_amount)
            category = ''
            # Mark as 'full' if paid amount is KES 1000 or more
            if paid_amount >= GRADUATION_FEE_TOTAL:
                category = 'full'
            elif paid_amount > 0:
                category = 'partial'
            else:
                category = 'none'

            if status_filter == 'all' or status_filter == category:
                report_data.append({
                    'name': student_db_obj.name,
                    'phone': student_db_obj.phone,  # Add phone number
                    'class': student_db_obj.class_name,
                    'status_category': category.capitalize(),
                    'amount_paid_kes': paid_amount
                })
        
        # Sort report data by class and then by name within each class
        report_data.sort(key=lambda x: (x['class'], x['name']))
        return report_data
    except Exception as e:
        print(f"Error in _get_filtered_report_data for class {class_id}, session {session_id_str}: {e}")
        return []

@main_routes.route('/api/mark-session-inactive', methods=['POST'])
def mark_session_inactive():
    """API endpoint to ensure only session 6 students are active."""
    try:
        # Get all students
        all_students = Student.query.all()
        updated_count = 0
        session_6_count = 0
        other_session_count = 0
        
        for student in all_students:
            # Get the session number
            session_number = student.session.split()[-1]
            try:
                session_number = int(session_number)
            except (ValueError, TypeError):
                print(f"Warning: Invalid session number format for student {student.name}")
                continue
            
            if session_number == 6:
                session_6_count += 1
                if not student.active:
                    student.active = True
                    updated_count += 1
            else:
                other_session_count += 1
                if student.active:
                    student.active = False
                    updated_count += 1

        db.session.commit()
        
        return jsonify({
            'message': f'Successfully updated student statuses. Only session 6 students are active.',
            'updated_count': updated_count,
            'session_6_count': session_6_count,
            'other_session_count': other_session_count
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@main_routes.route('/api/generate-report', methods=['GET'])
def generate_report_api():
    """API endpoint to generate and download a report on graduation fee status."""
    class_id = request.args.get('classId')
    status_filter = request.args.get('statusFilter', 'all') # 'all', 'full', 'partial', 'none'
    report_format = request.args.get('format', 'pdf') # 'pdf' or 'excel'

    # Get current date
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Handle "All Classes" case when class_id is empty
    if not class_id:
        class_name_display = 'All Classes'
    else:
        class_name_display = class_id

    session_id_str = request.args.get('sessionId')
    session_display = f"Session {session_id_str}" if session_id_str else "All Sessions"

    # Get filtered report data
    report_data = _get_filtered_report_data(class_id, status_filter, session_id_str)

    if not report_data:
        return jsonify({'message': 'No students match the selected criteria for the report.'}), 404

    if report_format == 'pdf':
        # Create PDF report with fpdf2
        pdf = FPDF()
        pdf.add_page('L')  # Landscape orientation
        pdf.set_auto_page_break(auto=True, margin=20)
        
        # Add logo (using freewa-8.png)
        try:
            pdf.image('static/images/freewa-8.png', x=10, y=10, w=30)
        except:
            pass  # If logo file is not found, just continue without it
        
        # Add title with better styling and reduced spacing
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Graduation Fee Status Report", 0, 1, "C")
        pdf.ln(5)
        
        # Add subtitle with reduced spacing
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 8, f"Class: {class_name_display}", 0, 1, "L")
        pdf.cell(0, 8, f"Session: {session_display}", 0, 1, "L")
        pdf.ln(5)
        
        # Add date with better styling and reduced spacing
        pdf.set_font("Arial", "I", 9)
        pdf.cell(0, 8, f"Generated on: {current_date}", 0, 1, "R")
        pdf.ln(10)
        
        # Define optimized column widths for better space utilization
        col_widths = {
            'S/N': 15,    # Smaller for serial numbers
            'Student Name': 90,  # Increased for better name visibility
            'Phone': 50,  # Reduced slightly
            'Class': 60,   # Kept the same
            'Status': 30,  # Kept the same
            'Amount Paid (KES)': 45  # Kept the same
        }
        
        # Calculate total width of all columns
        total_width = sum(col_widths.values())
        # Adjust each column width proportionally to fill the page width
        for key in col_widths:
            col_widths[key] = (col_widths[key] / total_width) * 270  # 270 is the width of A4 in landscape mode
        
        # Add table headers with better styling and reduced spacing
        headers = list(col_widths.keys())
        pdf.set_font("Arial", "B", 10)  # Reduced font size slightly
        pdf.set_fill_color(240, 240, 240)  # Light gray background
        pdf.set_text_color(0, 0, 0)  # Black text
        
        # Write headers
        for header in headers:
            pdf.cell(col_widths[header], 10, header, 1, 0, "C", 1)  # Reduced row height
        pdf.ln(1)  # Reduced spacing after headers
        
        # Add data rows with better styling and reduced spacing
        pdf.set_font("Arial", "", 9)  # Reduced font size slightly
        for idx, student in enumerate(report_data, start=1):
            # Set status color
            status_color = (0, 128, 0) if student['status_category'] == 'Full' else \
                         (255, 165, 0) if student['status_category'] == 'Partial' else \
                         (255, 0, 0)
            
            # Write row data with alternating row colors
            if idx % 2 == 0:
                pdf.set_fill_color(255, 255, 255)  # White
            else:
                pdf.set_fill_color(245, 245, 245)  # Very light gray
                
            # Write each cell
            pdf.set_text_color(0, 0, 0)  # Reset text color
            pdf.cell(col_widths['S/N'], 10, str(idx), 1, 0, "C", 1)  # Reduced row height
            pdf.cell(col_widths['Student Name'], 10, student['name'], 1, 0, "L", 1)  # Reduced row height
            pdf.cell(col_widths['Phone'], 10, student['phone'], 1, 0, "L", 1)  # Reduced row height
            pdf.cell(col_widths['Class'], 10, student['class'], 1, 0, "L", 1)  # Reduced row height
            
            # Set status cell color
            pdf.set_text_color(*status_color)
            pdf.cell(col_widths['Status'], 10, student['status_category'], 1, 0, "C", 1)  # Reduced row height
            
            # Reset text color
            pdf.set_text_color(0, 0, 0)
            pdf.cell(col_widths['Amount Paid (KES)'], 10, f"{student['amount_paid_kes']:.2f}", 1, 1, "R", 1)  # Reduced row height
            
        # Add footer with page number and date
        pdf.set_y(-20)
        pdf.set_font("Arial", "I", 8)
        # Get total number of pages
        pdf.alias_nb_pages()
        pdf.cell(0, 10, f"Page {pdf.page_no()} of {{nb}}", 0, 0, "C")
        pdf.set_y(-15)
        pdf.cell(0, 5, f"Generated on: {current_date}", 0, 0, "C")
        
        # Save PDF to buffer
        buffer = io.BytesIO()
        pdf.output(buffer)
        buffer.seek(0)
        
        return Response(
            buffer.getvalue(),
            mimetype='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename=graduation_fee_report_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf'
            }
        )

    # Excel format
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet()

    # Define formats
    title_format = workbook.add_format({
        'bold': True,
        'font_size': 16,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1
    })

    subtitle_format = workbook.add_format({
        'bold': True,
        'font_size': 12,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1
    })

    normal_format = workbook.add_format({
        'border': 1
    })

    # Add title and subtitle
    worksheet.merge_range('A1:F1', 'Graduation Fee Status Report', title_format)
    worksheet.merge_range('A2:F2', f'Class: {class_name_display}', subtitle_format)
    worksheet.merge_range('A3:F3', f'Session: {session_display}', subtitle_format)
    worksheet.merge_range('A4:F4', f'Generated on: {current_date}', subtitle_format)

    # Add space after title
    worksheet.set_row(4, 20)  # Empty row for spacing

    # Set column widths
    worksheet.set_column(0, 0, 10)  # Serial Number
    worksheet.set_column(1, 1, 30)  # Student Name
    worksheet.set_column(2, 2, 15)  # Phone
    worksheet.set_column(3, 3, 20)  # Class
    worksheet.set_column(4, 4, 15)  # Status
    worksheet.set_column(5, 5, 20)  # Amount Paid

    # Add header styles
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#D7E4BC',
        'border': 1,
        'align': 'center',
        'valign': 'vcenter'
    })

    # Add headers
    headers = ['S/N', 'Student Name', 'Phone', 'Class', 'Status', 'Amount Paid (KES)']
    for col_num, header in enumerate(headers):
        worksheet.write(5, col_num, header, header_format)

    # Add data with row numbering
    for row_num, student in enumerate(report_data, start=1):
        # Add serial number
        worksheet.write(5 + row_num, 0, row_num, header_format)
        
        # Add student data
        worksheet.write(5 + row_num, 1, student['name'], normal_format)
        worksheet.write(5 + row_num, 2, student['phone'], normal_format)
        worksheet.write(5 + row_num, 3, student['class'], normal_format)
        
        # Apply conditional formatting for status
        if student['status_category'] == 'Full':
            status_format = workbook.add_format({'bg_color': '#C6EFCE', 'bold': True})
        elif student['status_category'] == 'Partial':
            status_format = workbook.add_format({'bg_color': '#FFEB9C'})
        else:
            status_format = workbook.add_format({'bg_color': '#FFC7CE'})
        
        worksheet.write(5 + row_num, 4, student['status_category'], status_format)
        worksheet.write(5 + row_num, 5, student['amount_paid_kes'], normal_format)

    # Add borders to all cells
    for row in range(6, len(report_data) + 6):
        for col in range(6):
            # Get the value from our data instead of trying to get it from the worksheet
            if col == 0:
                value = row - 5  # Serial number
            elif col == 1:
                value = report_data[row - 6]['name']
            elif col == 2:
                value = report_data[row - 6]['phone']
            elif col == 3:
                value = report_data[row - 6]['class']
            elif col == 4:
                value = report_data[row - 6]['status_category']
            else:
                value = report_data[row - 6]['amount_paid_kes']
            
            worksheet.write(row, col, value, workbook.add_format({'border': 1}))

    workbook.close()
    output.seek(0)
    
    return Response(
        output.getvalue(),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={
            'Content-Disposition': f'attachment; filename=graduation_fee_report_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'
        }
    )

@main_routes.route('/api/class-distribution', methods=['GET'])
def get_class_distribution():
    """API endpoint to get class distribution data for chart."""
    try:
        # Query to get class distribution
        class_distribution = db.session.query(
            Student.class_name,
            func.count(Student.id).label('student_count')
        ).group_by(Student.class_name).all()
        
        # Prepare data for chart
        labels = []
        data = []
        
        for class_name, count in class_distribution:
            if class_name:  # Skip None or empty class names
                # Normalize class name
                normalized_name = class_name.strip().upper()
                if normalized_name not in labels:
                    labels.append(normalized_name)
                    data.append(count)
                else:
                    # If class name already exists, add the count
                    index = labels.index(normalized_name)
                    data[index] += count
        
        return jsonify({
            'labels': labels,
            'data': data
        })
    except Exception as e:
        print(f"Error fetching class distribution: {e}")
        return jsonify({'error': 'Could not fetch class distribution'}), 500

# --- How to Register this Blueprint ---
# In your main Flask application file (e.g., app.py or where you define `create_app()`):
#
# from flask import Flask
# # Adjust the import path based on your project structure:
# # from .test_routes import test_routesb-package of your app package
# # from project_name.routes import main_routes # If using a named project package
#
# def create_app():
#     app = Flask(__name__)
#     # ... other application configurations (database, SQLAlchemy, etc.) ...
#
#     # Import and register the blueprint
#     # Ensure the import path for main_routes is correct for your project structure
#     # For example, if this routes file is in e:\payments\routes\__init__.py
#     # and your app is created in e:\payments\app.py, you might use:
#     # from routes import main_routes
#     app.register_blueprint(main_routes) # You can add url_prefix, e.g., app.register_blueprint(main_routes, url_prefix='/payments')
#
#     return app
#
# if __name__ == '__main__':
#     # This is for direct execution (python routes/__init__.py), usually not how Flask apps are run.
#     # Typically, you'd have an app.py or run.py that calls create_app() and then app.run().
#     # For demonstration if you were to run this file directly (not recommended for a full app):
#     # temp_app = Flask(__name__)
#     # temp_app.register_blueprint(main_routes)
#     # temp_app.run(debug=True)
#     print("This blueprint should be registered with a Flask app instance.")
#     print("See comments at the end of the file for how to register it.")
