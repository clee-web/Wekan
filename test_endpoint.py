from flask import Flask
from models import db, Student
from routes import main_routes

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/academy.db'
db.init_app(app)

# Register the blueprint
app.register_blueprint(main_routes)

if __name__ == '__main__':
    with app.app_context():
        # Test the endpoint
        from flask import json
        from werkzeug.test import EnvironBuilder
        from werkzeug.wrappers import Request
        
        # Create a test request
        builder = EnvironBuilder(path='/api/mark-session-inactive', method='POST')
        env = builder.get_environ()
        request = Request(env)
        
        # Call the route directly
        response = main_routes.mark_session_inactive()
        print('Response:', response.get_json())
        
        # Check if the changes were applied
        session_6_students = Student.query.filter(Student.session.like('%6%')).all()
        other_session_students = Student.query.filter(~Student.session.like('%6%')).all()
        
        print('\nSession 6 students:')
        for student in session_6_students:
            print(f'{student.name}: Active={student.active}')
        
        print('\nOther session students:')
        for student in other_session_students:
            print(f'{student.name}: Active={student.active}')
