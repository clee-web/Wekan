from models import db, Admin

def seed_admin():
    admin = Admin.query.filter_by(username='admin').first()
    if not admin:
        admin = Admin(username='admin')
        admin.set_password('adminiyf')
        db.session.add(admin)
        db.session.commit()
        print('Admin user created: admin/adminiyf')
    else:
        admin.set_password('adminiyf')
        db.session.commit()
        print('Admin password reset to: adminiyf')

if __name__ == '__main__':
    from app import app
    with app.app_context():
        seed_admin()
