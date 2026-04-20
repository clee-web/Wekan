import requests
import json
from datetime import datetime
import logging
import os
from base64 import b64encode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MpesaAPI:
    def __init__(self):
        self.base_url = "https://sandbox.safaricom.co.ke"  # Change to production URL when going live
        self.auth_token = 'Basic S0R6Qzh0U0YxUVZiZEpOQkZPQTJVTFdHQjNHTkppM3FxYWlWUm1qOVZIVnFRbmFWOll2cDdWNUF6V1BRcnRjenpTT0ZyQWFya0JOajBuR3VHaklWNWQ4QlFOWVp4VkdoZDdadDNobU1PVnZtdGxhUkg='
        self._access_token = None

    def get_access_token(self):
        """Get OAuth access token from Safaricom"""
        try:
            headers = {
                'Authorization': self.auth_token
            }
            
            url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                self._access_token = response.json()['access_token']
                return True
            else:
                logger.error(f"Error getting access token: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error in get_access_token: {str(e)}")
            return False

    def stk_push(self, phone_number, amount, account_reference, transaction_desc="Payment"):
        """Initiate STK push for payment"""
        if not self._access_token:
            self.get_access_token()

        try:
            # Format phone number (remove leading 0 or +254)
            if phone_number.startswith("0"):
                phone_number = "254" + phone_number[1:]
            elif phone_number.startswith("+"):
                phone_number = phone_number[1:]

            # Get timestamp
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            
            headers = {
                "Authorization": f"Bearer {self._access_token}",
                "Content-Type": "application/json"
            }

            payload = {
                "BusinessShortCode": "174379",  # Lipa Na Mpesa Online Shortcode
                "Password": b64encode(f"174379{os.getenv('MPESA_PASSKEY')}{timestamp}".encode()).decode(),
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": int(amount),
                "PartyA": phone_number,
                "PartyB": "174379",  # Same as BusinessShortCode
                "PhoneNumber": phone_number,
                "CallBackURL": f"{os.getenv('BASE_URL', 'https://example.com')}/mpesa/callback",
                "AccountReference": account_reference,
                "TransactionDesc": transaction_desc
            }

            response = requests.post(
                f"{self.base_url}/mpesa/stkpush/v1/processrequest",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            return True, response.json()
        except Exception as e:
            logger.error(f"Error initiating STK push: {str(e)}")
            return False, str(e)

    def verify_transaction(self, checkout_request_id):
        """Verify the status of a transaction"""
        if not self._access_token:
            self.get_access_token()

        try:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            
            headers = {
                "Authorization": f"Bearer {self._access_token}",
                "Content-Type": "application/json"
            }

            payload = {
                "BusinessShortCode": "174379",
                "Password": b64encode(f"174379{os.getenv('MPESA_PASSKEY')}{timestamp}".encode()).decode(),
                "Timestamp": timestamp,
                "CheckoutRequestID": checkout_request_id
            }

            response = requests.post(
                f"{self.base_url}/mpesa/stkpushquery/v1/query",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            return True, response.json()
        except Exception as e:
            logger.error(f"Error verifying transaction: {str(e)}")
            return False, str(e)

# Initialize global instance
mpesa = MpesaAPI()
