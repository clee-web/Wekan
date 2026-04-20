from app import app
from models import Admin

with app.app_context():
    admins = Admin.query.all()
    print('Admins:', admins)
    for admin in admins:
        print('Username:', admin.username)
