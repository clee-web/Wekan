from app import app, db
from models import Payment

def add_total_fee_column():
    with app.app_context():
        try:
            # Try to add the column
            from sqlalchemy import text
            db.session.execute(text('ALTER TABLE payment ADD COLUMN total_fee FLOAT DEFAULT 1500.0 NOT NULL'))
            db.session.commit()
            print("Added total_fee column successfully")
        except Exception as e:
            if 'duplicate column name' in str(e).lower():
                print("Column total_fee already exists")
            else:
                print(f"Error: {e}")
                return

        # Update total_fee values based on payment type
        try:
            payments = Payment.query.all()
            for payment in payments:
                if payment.payment_type == 'Sign Language Advance':
                    payment.total_fee = 1300.0
                else:
                    payment.total_fee = 1500.0
                
                # Update payment status
                payment.update_status()
            
            db.session.commit()
            print("Updated payment total fees and statuses successfully")
        except Exception as e:
            print(f"Error updating payments: {e}")
            db.session.rollback()

if __name__ == '__main__':
    add_total_fee_column()
