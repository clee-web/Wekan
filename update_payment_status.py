from app import app, db
from models import Payment

def update_all_payment_statuses():
    with app.app_context():
        # Get all payments
        payments = Payment.query.all()
        
        # Update status for each payment
        for payment in payments:
            payment.update_status()
        
        # Commit all changes
        db.session.commit()
        print("All payment statuses have been updated successfully!")

if __name__ == '__main__':
    update_all_payment_statuses()
