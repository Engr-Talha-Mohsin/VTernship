import csv
from werkzeug.security import check_password_hash

class AdminAuth:
    @staticmethod
    def authenticate(email, password):
        try:
            with open('data/admin.csv', 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['email'] == email:
                        if check_password_hash(row['password'], password):
                            return {
                                'id': row['id'],
                                'name': row['name'],
                                'email': row['email']
                            }
        except FileNotFoundError:
            pass
        return None