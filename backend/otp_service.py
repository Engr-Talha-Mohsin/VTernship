import csv
import secrets
from datetime import datetime, timedelta
import os

class OTPService:
    def __init__(self, expiry_minutes=15):
        self.expiry_minutes = expiry_minutes
    
    def generate_otp(self, email, purpose):
        """Generate OTP and store it"""
        otp = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        expires_at = (datetime.now() + timedelta(minutes=self.expiry_minutes)).isoformat()
        
        otp_record = {
            'email': email,
            'otp': otp,
            'purpose': purpose,
            'expires_at': expires_at,
            'created_at': datetime.now().isoformat()
        }
        
        # Read existing OTPs
        otps = []
        if os.path.exists('data/otps.csv'):
            with open('data/otps.csv', 'r') as f:
                reader = csv.DictReader(f)
                otps = list(reader)
        
        # Remove old OTPs for this email and purpose
        otps = [o for o in otps if not (o['email'] == email and o['purpose'] == purpose)]
        
        # Add new OTP
        otps.append(otp_record)
        
        # Write back
        with open('data/otps.csv', 'w', newline='') as f:
            fieldnames = ['email', 'otp', 'purpose', 'expires_at', 'created_at']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(otps)
        
        return otp
    
    def verify_otp(self, email, otp, purpose):
        """Verify OTP"""
        if not os.path.exists('data/otps.csv'):
            return False
        
        with open('data/otps.csv', 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if (row['email'] == email and 
                    row['otp'] == otp and 
                    row['purpose'] == purpose):
                    
                    # Check expiry
                    expires_at = datetime.fromisoformat(row['expires_at'])
                    if datetime.now() < expires_at:
                        return True
        
        return False
    
    def invalidate_otp(self, email, otp):
        """Remove OTP after use"""
        if not os.path.exists('data/otps.csv'):
            return
        
        with open('data/otps.csv', 'r') as f:
            reader = csv.DictReader(f)
            otps = [row for row in reader if not (row['email'] == email and row['otp'] == otp)]
        
        with open('data/otps.csv', 'w', newline='') as f:
            fieldnames = ['email', 'otp', 'purpose', 'expires_at', 'created_at']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(otps)