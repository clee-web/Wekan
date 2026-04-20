from flask import Blueprint, request, jsonify
from models import db, Payment, Student
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
mpesa_bp = Blueprint('mpesa', __name__)

@mpesa_bp.route('/initiate-payment', methods=['POST'])
def initiate_payment():
    """Initiate M-PESA payment"""
    try:
        data = request.get_json()
        student_id = data.get('student_id')
        amount = data.get('amount')
        phone = data.get('phone')

        if not student_id or not amount or not phone:
            return jsonify({
                'success': False,
                'message': 'Missing required fields: student_id, amount, and phone'
            }), 400
            
        # Validate phone number format
        import re
        phone_regex = re.compile(r'^254[17][0-9]{8}$')
        
        # Format phone number if it starts with 0 or +254
        if phone.startswith('0'):
            phone = '254' + phone[1:]
        elif phone.startswith('+254'):
            phone = phone[1:]
            
        if not phone_regex.match(phone):
            return jsonify({
                'success': False,
                'message': 'Invalid phone number format. Must be a valid Safaricom number (07... or 01...)'
            }), 400

        # Get student details
        student = Student.query.get(student_id)
        if not student:
            return jsonify({
                'success': False,
                'message': 'Student not found'
            }), 404

        # Generate unique reference
        reference = f"PAY{student_id}{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Create pending payment record
        payment = Payment(
            student_id=student_id,
            transaction_number=reference,
            amount=amount,
            payment_type='Graduation Fee' if amount >= 1000 else 'Passport Fee',
            payment_method='mpesa',
            status='pending',
            year=datetime.now().strftime('%Y'),
            session='current',
            notes=f"M-PESA payment initiated for phone {phone}"
        )
        db.session.add(payment)
        db.session.commit()

        # Auto-sync to Supabase
        try:
            from supabase_sync import sync_payment_to_supabase
            sync_payment_to_supabase(payment)
        except Exception as e:
            print(f"Supabase sync error: {str(e)}")

        return jsonify({
            'success': True,
            'message': 'Payment initiated successfully',
            'payment_id': payment.id,
            'amount': amount
        })

    except Exception as e:
        logger.error(f"Error initiating payment: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500

@mpesa_bp.route('/callback', methods=['POST'])
def mpesa_callback():
    """Handle M-PESA callback"""
    try:
        # Get the callback data
        callback_data = request.get_json()
        
        # Log the callback for debugging
        logger.info(f"M-PESA callback received: {callback_data}")
        
        # Extract relevant information
        result_code = callback_data.get('Body', {}).get('stkCallback', {}).get('ResultCode')
        transaction_id = callback_data.get('Body', {}).get('stkCallback', {}).get('CallbackMetadata', {}).get('Item', [])[1].get('Value')
        
        # Find the latest pending payment for this transaction
        payment = Payment.query.filter_by(status='pending').order_by(Payment.date.desc()).first()
        
        if not payment:
            logger.error(f"No pending payment found")
            return jsonify({'success': False}), 400
            
        if result_code == 0:  # Successful payment
            # Update payment details
            payment.status = 'cleared'
            payment.transaction_number = transaction_id
            payment.notes = f"M-PESA payment successful. Transaction ID: {transaction_id}"
            
            # Get callback items for amount
            callback_items = callback_data.get('Body', {}).get('stkCallback', {}).get('CallbackMetadata', {}).get('Item', [])
            
            # Extract amount if available
            for item in callback_items:
                if item.get('Name') == 'Amount':
                    payment.amount = float(item.get('Value', 0))
            
            # Update payment status for all student's payments
            payment.update_status()
            
            db.session.commit()
            logger.info(f"Payment {payment.id} processed successfully")
        else:
            # Payment failed
            payment.status = 'failed'
            payment.notes = f"M-PESA payment failed: {callback_data.get('Body', {}).get('stkCallback', {}).get('ResultDesc')}"
            db.session.commit()
            logger.warning(f"Payment {payment.id} failed: {payment.notes}")
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error processing M-PESA callback: {str(e)}")
        return jsonify({'success': False}), 500

@mpesa_bp.route('/check-payment-status/<payment_id>', methods=['GET'])
def check_payment_status(payment_id):
    """Check payment status"""
    try:
        payment = Payment.query.get(payment_id)
        if not payment:
            return jsonify({
                'success': False,
                'message': 'Payment not found'
            }), 404

        return jsonify({
            'success': True,
            'status': payment.status,
            'amount': payment.amount,
            'transaction_number': payment.transaction_number
        })

    except Exception as e:
        logger.error(f"Error checking payment status: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500
