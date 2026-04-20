"""Reset admin password to fix scrypt hash issue on Render"""
from app import app, db
from models import Admin

with app.app_context():
    admin = Admin.query.filter_by(username='admin').first()
    if admin:
        admin.set_password('adminiyf')
        db.session.commit()
        print('Admin password reset successfully to: adminiyf')
    else:
        # Create admin if doesn't exist
        admin = Admin(username='admin')
        admin.set_password('adminiyf')
        db.session.add(admin)
        db.session.commit()
        print('Admin user created: admin/adminiyf')
