import csv
import os


class CSVHandler:

    @staticmethod
    def read_csv(filepath):
        """Return all rows as list of dicts"""
        if not os.path.exists(filepath):
            return []

        with open(filepath, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)

    @staticmethod
    def write_csv(filepath, data):
        """Overwrite CSV with provided rows"""

        # If data empty, still keep header
        if not data:
            headers = []

            if os.path.exists(filepath):
                with open(filepath, "r", newline="", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    headers = next(reader, [])

            with open(filepath, "w", newline="", encoding="utf-8") as f:
                if headers:
                    writer = csv.writer(f)
                    writer.writerow(headers)
            return

        fieldnames = data[0].keys()

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

    @staticmethod
    def append_row(filepath, row, fieldnames=None):
        """Append one row to CSV"""
        file_exists = os.path.exists(filepath)

        if not fieldnames:
            fieldnames = row.keys()

        with open(filepath, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            # Write header if file does not exist
            if not file_exists:
                writer.writeheader()

            writer.writerow(row)

    @staticmethod
    def find_by_email(filepath, email):
        """Find record by email"""
        data = CSVHandler.read_csv(filepath)

        for row in data:
            if row.get("email") == email:
                return row

        return None

    @staticmethod
    def find_by_field(filepath, field, value):
        """Find row by any column"""
        data = CSVHandler.read_csv(filepath)

        for row in data:
            if row.get(field) == value:
                return row

        return None

    @staticmethod
    def update_row(filepath, key_field, key_value, updates):
        """Update row where key_field == key_value"""

        data = CSVHandler.read_csv(filepath)
        updated = False

        for row in data:
            if row.get(key_field) == key_value:
                row.update(updates)
                updated = True
                break

        if updated:
            CSVHandler.write_csv(filepath, data)

        return updated
