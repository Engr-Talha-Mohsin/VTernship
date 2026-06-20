import csv
import uuid
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import re

class StudentAuth:
    @staticmethod
    def signup(first_name, last_name, email, password):
        # Validate email
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return {'success': False, 'message': 'Invalid email format'}
        
        # Check if email already exists
        try:
            with open('data/students.csv', 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['email'] == email:
                        return {'success': False, 'message': 'Email already registered'}
        except FileNotFoundError:
            pass
        
        # Create new student
        student_id = str(uuid.uuid4())
        hashed_password = generate_password_hash(password)
        
        student = {
            'id': student_id,
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'password': hashed_password,
            'verified': 'false',
            'skills': '',
            'created_at': datetime.now().isoformat()
        }
        
        # Append to CSV
        file_exists = False
        try:
            with open('data/students.csv', 'r') as f:
                file_exists = True
        except FileNotFoundError:
            file_exists = False
        
        with open('data/students.csv', 'a', newline='') as f:
            fieldnames = ['id', 'first_name', 'last_name', 'email', 'password', 'verified', 'skills', 'created_at']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
            writer.writerow(student)
        
        return {'success': True, 'message': 'Student account created'}
    
    @staticmethod
    def authenticate(email, password):
        try:
            with open('data/students.csv', 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['email'] == email:
                        if row['verified'] != 'true':
                            return None  # Not verified
                        
                        if check_password_hash(row['password'], password):
                            return {
                                'id': row['id'],
                                'first_name': row['first_name'],
                                'last_name': row['last_name'],
                                'email': row['email'],
                                'verified': row['verified'],
                                'skills': row['skills']
                            }
        except FileNotFoundError:
            pass
        return None