import csv
import re
import uuid
from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash


class CompanyAuth:
    @staticmethod
    def signup(company_name, email, password, phone, website, industry, address):
        # Validate email
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return {'success': False, 'message': 'Invalid email format'}
        
        # Check if email already exists
        try:
            with open('data/companies.csv', 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['email'] == email:
                        return {'success': False, 'message': 'Email already registered'}
        except FileNotFoundError:
            pass
        
        # Create new company
        company_id = str(uuid.uuid4())
        hashed_password = generate_password_hash(password)
        
        company = {
            'id': company_id,
            'company_name': company_name,
            'email': email,
            'password': hashed_password,
            'phone': phone,
            'website': website,
            'industry': industry,
            'address': address,
            'verified': 'false',
            'approved': 'false',
            'created_at': datetime.now().isoformat()
        }
        
        # Append to CSV
        file_exists = False
        try:
            with open('data/companies.csv', 'r') as f:
                file_exists = True
        except FileNotFoundError:
            file_exists = False
        
        with open('data/companies.csv', 'a', newline='') as f:
            fieldnames = ['id', 'company_name', 'email', 'password', 'phone', 'website', 'industry', 'address', 'verified', 'approved', 'created_at']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
            writer.writerow(company)
        
        return {'success': True, 'message': 'Company account created'}
    
    @staticmethod
    def authenticate(email, password):
        try:
            with open('data/companies.csv', 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['email'] == email:
                        if row['verified'] != 'true':
                            return None  # Not verified
                        
                        if row['approved'] != 'true':
                            return {'blocked': True, 'message': 'Account not approved by admin yet'}
                        
                        if check_password_hash(row['password'], password):
                            return {
                                'id': row['id'],
                                'company_name': row['company_name'],
                                'email': row['email'],
                                'phone': row['phone'],
                                'website': row['website'],
                                'industry': row['industry'],
                                'address': row['address'],
                                'verified': row['verified'],
                                'approved': row['approved']   # ✅ critical
                            }
                            
        except FileNotFoundError:
            pass
        return None           