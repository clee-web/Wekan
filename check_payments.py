from app import app, db
from models import Payment, Student

def check_student_payments():
    with app.app_context():
        # Get all students
        students = Student.query.all()
        
        duplicates_found = 0
        
        for student in students:
            print(f"\nStudent: {student.name} (ID: {student.id})")
            
            # Get all payments for this student
            payments = Payment.query.filter_by(student_id=student.id).all()
            
            total_paid = sum(payment.amount for payment in payments)
            
            print(f"Total Paid: KES {total_paid:.2f}")
            print("Individual Payments:")
            for payment in payments:
                print(f"- Type: {payment.payment_type}, Amount: KES {payment.amount:.2f}, Status: {payment.status}")
            
            # Check for duplicates
            dups = Payment.find_duplicates(student_id=student.id)
            if dups:
                duplicates_found += sum(d[6] for d in dups)  # sum counts
                print(f"⚠️  FOUND {len(dups)} duplicate group(s)! Run: python remove_duplicates.py --student {student.id} --dry-run")
            
            # Force update status for all payments
            for payment in payments:
                old_status = payment.status
                payment.update_status()
                if old_status != payment.status:
                    print(f"Status changed from {old_status} to {payment.status}")
            
            db.session.commit()
        
        print(f"\n=== SUMMARY ===")
        print(f"Total students checked: {len(students)}")
        print(f"Duplicate records found: {duplicates_found}")
        if duplicates_found > 0:
            print("Run: python remove_duplicates.py --execute")

if __name__ == '__main__':
    check_student_payments()

