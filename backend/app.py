import csv
import io
import os
import re
import secrets
import uuid
from datetime import datetime, timedelta

from admin_auth import AdminAuth
from company_auth import CompanyAuth
from csv_handler import CSVHandler
from email_service import EmailService
from flask import (
    Flask,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from flask_session import Session
from otp_service import OTPService
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from session_manager import SessionManager

# Import custom modules
from student_auth import StudentAuth
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__, static_folder="../frontend", static_url_path="")

# ---------------- MAIL CONFIG ----------------

# ---------------- SECRET KEY ----------------
app.secret_key = "4cc6d657813c0e4088d86e6306e981e09f4b01eef210ee37f0fac75ccdf6d1c5"

# ---------------- SESSION CONFIG ----------------
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = "./flask_session"
app.config["SESSION_PERMANENT"] = True
app.config["SESSION_USE_SIGNER"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=24)

# Cookie settings
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = False
app.config["SESSION_COOKIE_HTTPONLY"] = True  # keep False for localhost
# Limit upload size (5MB)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
Session(app)

# ---------------- CORS ----------------

# Initialize services
csv_handler = CSVHandler()
otp_service = OTPService()
email_service = EmailService()
session_manager = SessionManager()

# Ensure data directory exists
os.makedirs("data", exist_ok=True)
os.makedirs("datasets", exist_ok=True)
os.makedirs("cv_uploads", exist_ok=True)


# Initialize CSV files if they don't exist
def init_csv_files():
    # Students CSV
    if not os.path.exists("data/students.csv"):
        with open("data/students.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "id",
                    "first_name",
                    "last_name",
                    "email",
                    "password",
                    "verified",
                    "skills",
                    "created_at",
                ]
            )

    # Companies CSV
    if not os.path.exists("data/companies.csv"):
        with open("data/companies.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "id",
                    "company_name",
                    "email",
                    "password",
                    "phone",
                    "website",
                    "industry",
                    "address",
                    "verified",
                    "approved",
                    "created_at",
                ]
            )

    # Admin CSV (pre-populate with one admin)
    if not os.path.exists("data/admin.csv"):
        with open("data/admin.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "name", "email", "password", "created_at"])
            # Add default admin (password: Admin@123)
            hashed_pw = generate_password_hash("Admin@123")
            writer.writerow(
                [
                    str(uuid.uuid4()),
                    "System Admin",
                    "admin@vternship.com",
                    hashed_pw,
                    datetime.now().isoformat(),
                ]
            )

    # OTPs CSV
    if not os.path.exists("data/otps.csv"):
        with open("data/otps.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["email", "otp", "purpose", "expires_at", "created_at"])

    # Activity CSV

    if not os.path.exists("data/activity.csv"):
        with open("data/activity.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "type", "message", "created_at"])

    # Internships CSV
    if not os.path.exists("data/internships.csv"):
        with open("data/internships.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "internship_id",
                    "company_id",
                    "company_name",
                    "title",
                    "description",
                    "skills",
                    "deadline",
                    "dataset_file",
                    "status",
                    "max_positions",
                    "created_at",
                ]
            )

    # Applications CSV
    if not os.path.exists("data/applications.csv"):
        with open("data/applications.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "application_id",
                    "internship_id",
                    "company_id",
                    "student_id",
                    "student_name",
                    "email",
                    "skills",
                    "cover_letter",
                    "cv_file",
                    "status",
                    "applied_at",
                ]
            )
    if not os.path.exists("data/notifications.csv"):
        with open("data/notifications.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "user_id", "message", "created_at"])


def validate_dataset(path):
    required = [
        "task_id",
        "difficulty_level",
        "task_title",
        "task_description",
        "expected_output",
        "evaluation_criteria",
    ]

    # Try utf-8 first, fallback to latin1
    try:
        f = open(path, newline="", encoding="utf-8")
        reader = csv.DictReader(f)
        rows = list(reader)
    except UnicodeDecodeError:
        f = open(path, newline="", encoding="latin-1")
        reader = csv.DictReader(f)
        rows = list(reader)

    if set(reader.fieldnames or []) != set(required):
        return False, "Dataset headers invalid"

    counts = {"easy": 0, "medium": 0, "hard": 0}

    for row in rows:
        level = row["difficulty_level"].lower()
        if level not in counts:
            return False, "Invalid difficulty level"
        counts[level] += 1

    if counts["easy"] != 40:
        return False, "Need 40 easy tasks"
    if counts["medium"] != 45:
        return False, "Need 45 medium tasks"
    if counts["hard"] != 90:
        return False, "Need 90 hard tasks"

    return True, "valid"


# Routes
@app.route("/")
def home():
    return app.send_static_file("index.html")


@app.route("/api/auth/signin", methods=["POST"])
def signin():
    data = request.json
    role = data.get("role")
    email = data.get("email")
    password = data.get("password")

    if not all([role, email, password]):
        return jsonify({"success": False, "message": "All fields are required"}), 400

    user = None
    if role == "student":
        user = StudentAuth.authenticate(email, password)
    elif role == "company":
        user = CompanyAuth.authenticate(email, password)
    elif role == "admin":
        user = AdminAuth.authenticate(email, password)

    if user:
        # Set session
        session_manager.create_session(user, role)
        return jsonify(
            {"success": True, "message": "Login successful", "user": user, "role": role}
        )

    return jsonify({"success": False, "message": "Invalid credentials"}), 401


@app.route("/api/auth/student-signup", methods=["POST"])
def student_signup():
    data = request.json
    required_fields = [
        "first_name",
        "last_name",
        "email",
        "password",
        "confirm_password",
    ]

    for field in required_fields:
        if not data.get(field):
            return (
                jsonify(
                    {
                        "success": False,
                        "message": f'{field.replace("_", " ").title()} is required',
                    }
                ),
                400,
            )

    if data["password"] != data["confirm_password"]:
        return jsonify({"success": False, "message": "Passwords do not match"}), 400

    if len(data["password"]) < 8:
        return (
            jsonify(
                {"success": False, "message": "Password must be at least 8 characters"}
            ),
            400,
        )

    result = StudentAuth.signup(
        data["first_name"], data["last_name"], data["email"], data["password"]
    )

    if result["success"]:
        # Generate verification OTP
        otp = otp_service.generate_otp(data["email"], "verification")
        # Send verification email
        email_service.send_verification_email(data["email"], data["first_name"], otp)

        return jsonify(
            {
                "success": True,
                "message": "Account created successfully. Please check your email for verification.",
                "email": data["email"],
            }
        )

    return jsonify(result), 400


@app.route("/api/auth/company-signup", methods=["POST"])
def company_signup():
    data = request.json
    required_fields = [
        "company_name",
        "email",
        "password",
        "confirm_password",
        "phone",
        "website",
        "industry",
        "address",
    ]

    for field in required_fields:
        if not data.get(field):
            return (
                jsonify(
                    {
                        "success": False,
                        "message": f'{field.replace("_", " ").title()} is required',
                    }
                ),
                400,
            )

    if data["password"] != data["confirm_password"]:
        return jsonify({"success": False, "message": "Passwords do not match"}), 400

    result = CompanyAuth.signup(
        data["company_name"],
        data["email"],
        data["password"],
        data["phone"],
        data["website"],
        data["industry"],
        data["address"],
    )

    if result["success"]:
        otp = otp_service.generate_otp(data["email"], "verification")
        email_service.send_verification_email(data["email"], data["company_name"], otp)

        return jsonify(
            {
                "success": True,
                "message": "Company account created. Please verify your email and wait for admin approval.",
                "email": data["email"],
            }
        )

    return jsonify(result), 400


@app.route("/api/auth/verify-email", methods=["POST"])
def verify_email():
    data = request.json
    email = data.get("email")
    otp = data.get("otp")

    if not all([email, otp]):
        return jsonify({"success": False, "message": "Email and OTP are required"}), 400

    if otp_service.verify_otp(email, otp, "verification"):
        # Mark as verified in appropriate CSV
        for csv_file in ["students.csv", "companies.csv"]:
            users = csv_handler.read_csv(f"data/{csv_file}")
            for user in users:
                if user["email"] == email:
                    user["verified"] = "true"
                    csv_handler.write_csv(f"data/{csv_file}", users)
                    break

        return jsonify({"success": True, "message": "Email verified successfully"})

    return jsonify({"success": False, "message": "Invalid or expired OTP"}), 400


@app.route("/api/auth/forgot-password", methods=["POST"])
def forgot_password():
    email = request.json.get("email")

    if not email:
        return jsonify({"success": False, "message": "Email is required"}), 400

    # Check if email exists
    users = []
    for csv_file in ["students.csv", "companies.csv", "admin.csv"]:
        users.extend(csv_handler.read_csv(f"data/{csv_file}"))

    if not any(user["email"] == email for user in users):
        return jsonify({"success": False, "message": "Email not found"}), 404

    otp = otp_service.generate_otp(email, "password_reset")
    email_service.send_password_reset_email(email, otp)

    return jsonify(
        {"success": True, "message": "Password reset OTP sent to your email"}
    )


@app.route("/api/auth/reset-password", methods=["POST"])
def reset_password():
    data = request.json
    email = data.get("email")
    otp = data.get("otp")
    new_password = data.get("new_password")

    if not all([email, otp, new_password]):
        return jsonify({"success": False, "message": "All fields are required"}), 400

    if not otp_service.verify_otp(email, otp, "password_reset"):
        return jsonify({"success": False, "message": "Invalid or expired OTP"}), 400

    # Update password in appropriate CSV
    for csv_file in ["students.csv", "companies.csv", "admin.csv"]:
        users = csv_handler.read_csv(f"data/{csv_file}")
        updated = False
        for user in users:
            if user["email"] == email:
                user["password"] = generate_password_hash(new_password)
                updated = True
                break

        if updated:
            csv_handler.write_csv(f"data/{csv_file}", users)
            otp_service.invalidate_otp(email, otp)
            return jsonify({"success": True, "message": "Password reset successfully"})

    return jsonify({"success": False, "message": "User not found"}), 404


@app.route("/api/auth/check-session", methods=["GET"])
def check_session():
    user = session_manager.get_current_user()
    if user:
        return jsonify(
            {
                "success": True,
                "authenticated": True,
                "user": user["user"],
                "role": user["role"],
            }
        )
    return jsonify({"success": False, "authenticated": False})


@app.route("/api/auth/signout", methods=["POST"])
def signout():
    session_manager.destroy_session()
    return jsonify({"success": True, "message": "Signed out successfully"})


@app.route("/api/admin/companies", methods=["GET"])
def get_companies():
    user = session_manager.get_current_user()
    if not user or user["role"] != "admin":
        return jsonify({"success": False, "message": "Unauthorized"}), 403

    companies = csv_handler.read_csv("data/companies.csv")
    return jsonify({"success": True, "companies": companies})


@app.route("/api/admin/update-company-status", methods=["POST"])
def update_company_status():
    user = session_manager.get_current_user()

    # Admin authorization check
    if not user or user["role"] != "admin":
        return jsonify({"success": False, "message": "Unauthorized"}), 403

    data = request.json
    company_id = data.get("company_id")
    field = data.get("field")
    value = data.get("value")

    if not all([company_id, field, value]):
        return jsonify({"success": False, "message": "Missing parameters"}), 400

    companies = csv_handler.read_csv("data/companies.csv")
    updated = False
    updated_company = None

    for company in companies:
        if company["id"] == company_id:
            company[field] = value
            updated = True
            updated_company = company

            # Send approval email if approved
            if field == "approved" and value == "true":
                email_service.send_approval_email(
                    company["email"], company["company_name"]
                )

                log_activity(
                    "company_approved",
                    f"Company '{company['company_name']}' approved by admin",
                )

            # Log unapproval
            if field == "approved" and value == "false":
                log_activity(
                    "company_unapproved",
                    f"Company '{company['company_name']}' approval removed",
                )

            break

    if updated:
        csv_handler.write_csv("data/companies.csv", companies)

        # ✅ refresh active company session if logged in
        current = session_manager.get_current_user()
        if (
            current
            and current["role"] == "company"
            and current["user"]["id"] == company_id
        ):
            session_manager.create_session(updated_company, "company")

        return jsonify(
            {"success": True, "message": "Company status updated successfully"}
        )

    return jsonify({"success": False, "message": "Company not found"}), 404


@app.route("/api/admin/students", methods=["GET"])
def get_students():
    user = session_manager.get_current_user()

    if not user or user["role"] != "admin":
        return jsonify({"success": False, "message": "Unauthorized"}), 403

    students = csv_handler.read_csv("data/students.csv")

    # latest first
    students.reverse()

    return jsonify({"success": True, "students": students})


@app.route("/api/user/update-profile", methods=["POST"])
def update_profile():
    user = session_manager.get_current_user()
    if not user:
        return jsonify({"success": False, "message": "Unauthorized"}), 403

    data = request.json

    role_map = {
        "student": "students.csv",
        "company": "companies.csv",
        "admin": "admin.csv",
    }

    csv_file = f"data/{role_map[user['role']]}"
    users = csv_handler.read_csv(csv_file)

    updated = False

    for u in users:
        if u["email"] == user["user"]["email"]:
            for key, value in data.items():
                if key in u and key not in ["id", "email", "password"]:
                    u[key] = value
            updated = True
            break

    if updated:
        csv_handler.write_csv(csv_file, users)

        # ✅ Update session data
        session_user = session_manager.get_current_user()
        if session_user:
            session_user["user"].update(data)
            session["user"] = session_user["user"]

        return jsonify({"success": True, "message": "Profile updated successfully"})

    return jsonify({"success": False, "message": "User not found"}), 404


@app.route("/api/admin/activity", methods=["GET"])
def get_activity():
    user = session_manager.get_current_user()

    if not user or user["role"] != "admin":
        return jsonify({"success": False, "message": "Unauthorized"}), 403

    activity = csv_handler.read_csv("data/activity.csv")
    activity.reverse()

    return jsonify({"success": True, "activity": activity[:10]})


def log_activity(activity_type, message):
    activities = csv_handler.read_csv("data/activity.csv")

    activities.append(
        {
            "id": str(uuid.uuid4()),
            "type": activity_type,
            "message": message,
            "created_at": datetime.now().isoformat(),
        }
    )

    csv_handler.write_csv("data/activity.csv", activities)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


@app.route("/api/admin/download/students")
def download_students():
    user = session_manager.get_current_user()
    if not user or user["role"] != "admin":
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    log_activity("download", "Students CSV downloaded")
    file_path = os.path.join(BASE_DIR, "data", "students.csv")
    return send_file(file_path, as_attachment=True)


@app.route("/api/admin/download/companies")
def download_companies():
    user = session_manager.get_current_user()
    if not user or user["role"] != "admin":
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    log_activity("download", "Companies CSV downloaded")

    file_path = os.path.join(BASE_DIR, "data", "companies.csv")
    return send_file(file_path, as_attachment=True)


@app.route("/api/admin/students/pdf")
def download_students_pdf():

    user = session_manager.get_current_user()
    if not user or user["role"] != "admin":
        return jsonify({"success": False, "message": "Unauthorized"}), 403

    # ✅ ADD HERE
    log_activity("download", "Students PDF downloaded")

    file_path = os.path.join(BASE_DIR, "data", "students.csv")

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    y = 750
    c.setFont("Helvetica", 10)

    with open(file_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            text = f"{row['first_name']} {row['last_name']} | {row['email']} | {row['skills']}"
            c.drawString(40, y, text)

            y -= 20
            if y < 50:
                c.showPage()
                c.setFont("Helvetica", 10)
                y = 750

    c.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="students.pdf",
        mimetype="application/pdf",
    )


@app.route("/api/admin/companies/pdf")
def download_companies_pdf():

    user = session_manager.get_current_user()
    if not user or user["role"] != "admin":
        return jsonify({"success": False, "message": "Unauthorized"}), 403

    # ✅ ADD HERE
    log_activity("download", "Companies PDF downloaded")

    file_path = os.path.join(BASE_DIR, "data", "companies.csv")

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    y = 750
    c.setFont("Helvetica", 10)

    with open(file_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            text = f"{row['company_name']} | {row['email']} | {row['industry']}"
            c.drawString(40, y, text)

            y -= 20
            if y < 50:
                c.showPage()
                c.setFont("Helvetica", 10)
                y = 750

    c.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="companies.pdf",
        mimetype="application/pdf",
    )


@app.route("/api/company/create-internship", methods=["POST"])
def create_internship():
    user = session_manager.get_current_user()
    if not user or user["role"] != "company":
        return jsonify({"success": False}), 403

    file = request.files.get("dataset")
    if not file:
        return jsonify({"success": False, "message": "Dataset required"}), 400

    filename = str(uuid.uuid4()) + ".csv"
    path = os.path.join("datasets", filename)
    file.save(path)

    valid, msg = validate_dataset(path)
    if not valid:
        os.remove(path)
        return jsonify({"success": False, "message": msg})

    internships = csv_handler.read_csv("data/internships.csv")

    internships.append(
        {
            "internship_id": str(uuid.uuid4()),
            "company_id": user["user"]["id"],
            "company_name": user["user"]["company_name"],
            "title": request.form["title"],
            "description": request.form["description"],
            "skills": request.form["skills"],
            "deadline": request.form["deadline"],
            "dataset_file": filename,
            "status": "open",
            "max_positions": request.form.get("max_positions", "5"),
            "created_at": datetime.now().isoformat(),
        }
    )

    csv_handler.write_csv("data/internships.csv", internships)

    return jsonify({"success": True, "message": "Internship created"})


@app.route("/api/student/apply", methods=["POST"])
def apply():
    user = session_manager.get_current_user()

    if not user or user["role"] != "student":
        return jsonify({"success": False}), 403

    form = request.form
    cv = request.files.get("cv")

    required_fields = ["internship_id", "name", "email", "skills", "cover_letter"]

    for f in required_fields:
        if not form.get(f):
            return jsonify({"success": False, "message": f"{f} required"}), 400

    if not cv:
        return jsonify({"success": False, "message": "CV required"}), 400

    # Allow only PDF
    if not cv.filename.lower().endswith(".pdf"):
        return jsonify({"success": False, "message": "Only PDF allowed"}), 400

    filename = str(uuid.uuid4()) + ".pdf"
    path = os.path.join("cv_uploads", filename)
    cv.save(path)

    internships = csv_handler.read_csv("data/internships.csv")

    internship = next(
        (i for i in internships if i["internship_id"] == form["internship_id"]),
        None,
    )

    if not internship:
        return jsonify({"success": False, "message": "Internship not found"}), 404

    if internship["status"] != "open":
        return jsonify({"success": False, "message": "Internship closed"}), 400

    apps = csv_handler.read_csv("data/applications.csv")

    for a in apps:
        if (
            a["internship_id"] == internship["internship_id"]
            and a["student_id"] == user["user"]["id"]
        ):
            return jsonify({"success": False, "message": "Already applied"}), 400

    apps.append(
        {
            "application_id": str(uuid.uuid4()),
            "internship_id": internship["internship_id"],
            "company_id": internship["company_id"],
            "student_id": user["user"]["id"],
            "student_name": form["name"],
            "email": form["email"],
            "skills": form["skills"],
            "cover_letter": form["cover_letter"],
            "cv_file": filename,
            "status": "pending",
            "applied_at": datetime.now().isoformat(),
        }
    )

    csv_handler.write_csv("data/applications.csv", apps)

    return jsonify({"success": True})


@app.route("/api/student/applications")
def student_apps():
    user = session_manager.get_current_user()

    if not user or user["role"] != "student":
        return jsonify({"success": False}), 403

    apps = csv_handler.read_csv("data/applications.csv")

    return jsonify([a for a in apps if a["student_id"] == user["user"]["id"]])


@app.route("/api/internships", methods=["GET"])
def list_internships():
    internships = csv_handler.read_csv("data/internships.csv")
    companies = csv_handler.read_csv("data/companies.csv")

    company_map = {c["id"]: c for c in companies}

    open_internships = []

    for i in internships:
        if i["status"] == "open":
            company = company_map.get(i["company_id"], {})

            open_internships.append(
                {**i, "company_name": company.get("company_name", "")}
            )

    return jsonify({"success": True, "internships": open_internships})


@app.route("/api/company/internships")
def company_internships():
    user = session_manager.get_current_user()

    if not user or user["role"] != "company":
        return jsonify({"success": False}), 403

    internships = csv_handler.read_csv("data/internships.csv")

    company_data = [i for i in internships if i["company_id"] == user["user"]["id"]]

    return jsonify({"success": True, "internships": company_data})


@app.route("/api/company/edit-internship", methods=["POST"])
def edit_internship():
    user = session_manager.get_current_user()

    if not user or user["role"] != "company":
        return jsonify({"success": False}), 403

    data = request.json
    iid = data.get("internship_id")

    internships = csv_handler.read_csv("data/internships.csv")

    updated = False

    for i in internships:
        if i["internship_id"] == iid:

            if i["company_id"] != user["user"]["id"]:
                return jsonify({"success": False}), 403

            i["title"] = data.get("title", i["title"])
            i["description"] = data.get("description", i["description"])
            i["skills"] = data.get("skills", i["skills"])
            i["deadline"] = data.get("deadline", i["deadline"])

            updated = True
            break

    if not updated:
        return jsonify({"success": False, "message": "Not found"}), 404

    csv_handler.write_csv("data/internships.csv", internships)

    return jsonify({"success": True})


@app.route("/api/company/close-internship", methods=["POST"])
def close_internship():
    user = session_manager.get_current_user()

    if not user or user["role"] != "company":
        return jsonify({"success": False}), 403

    iid = request.json.get("internship_id")

    internships = csv_handler.read_csv("data/internships.csv")

    updated = False

    for i in internships:
        if i["internship_id"] == iid:

            if i["company_id"] != user["user"]["id"]:
                return jsonify({"success": False}), 403

            # toggle status
            i["status"] = "closed" if i["status"] == "open" else "open"
            updated = True
            break

    if not updated:
        return jsonify({"success": False, "message": "Not found"}), 404

    csv_handler.write_csv("data/internships.csv", internships)

    return jsonify({"success": True})


@app.route("/api/company/delete-internship", methods=["POST"])
def delete_internship():
    user = session_manager.get_current_user()

    if not user or user["role"] != "company":
        return jsonify({"success": False}), 403

    iid = request.json.get("internship_id")

    internships = csv_handler.read_csv("data/internships.csv")

    # filter internships
    internships = [
        i
        for i in internships
        if not (i["internship_id"] == iid and i["company_id"] == user["user"]["id"])
    ]

    # --- FIX: force rewrite CSV even if empty ---
    csv_handler.write_csv("data/internships.csv", internships)

    # ---- DELETE APPLICATIONS ----
    apps = csv_handler.read_csv("data/applications.csv")

    for a in apps:
        if a["internship_id"] == iid:
            cv_file = a.get("cv_file")
            if cv_file:
                cv_path = os.path.join("cv_uploads", cv_file)
                if os.path.exists(cv_path):
                    os.remove(cv_path)

    apps = [a for a in apps if a["internship_id"] != iid]
    csv_handler.write_csv("data/applications.csv", apps)

    # ---- DELETE ACCEPTED ----
    accepted = csv_handler.read_csv("data/accepted_applications.csv")
    accepted = [a for a in accepted if a["internship_id"] != iid]

    csv_handler.write_csv("data/internships.csv", internships)

    return jsonify({"success": True})


@app.route("/api/company/applications")
def company_applications():
    user = session_manager.get_current_user()

    if not user or user["role"] != "company":
        return jsonify({"success": False}), 403

    apps = csv_handler.read_csv("data/applications.csv")

    company_apps = [a for a in apps if a["company_id"] == user["user"]["id"]]

    return jsonify({"success": True, "applications": company_apps})


@app.route("/api/company/application-status", methods=["POST"])
def update_application_status():
    user = session_manager.get_current_user()

    if not user or user["role"] != "company":
        return jsonify({"success": False}), 403

    data = request.json or {}
    app_id = data.get("application_id")
    status = data.get("status")

    if not app_id or status not in ["pending", "accepted", "rejected"]:
        return jsonify({"success": False, "message": "Invalid request"}), 400

    apps = csv_handler.read_csv("data/applications.csv")
    internships = csv_handler.read_csv("data/internships.csv")
    accepted = csv_handler.read_csv("data/accepted_applications.csv")

    # -------- FIND APPLICATION --------
    updated_app = next(
        (
            a
            for a in apps
            if a["application_id"] == app_id and a["company_id"] == user["user"]["id"]
        ),
        None,
    )

    if not updated_app:
        return jsonify({"success": False, "message": "Application not found"}), 404

    updated_app["status"] = status

    internship = next(
        (i for i in internships if i["internship_id"] == updated_app["internship_id"]),
        None,
    )

    if not internship:
        return jsonify({"success": False, "message": "Internship not found"}), 404

    # -------- ACCEPT LOGIC --------
    if status == "accepted":
        current_count = len(
            [x for x in accepted if x["internship_id"] == internship["internship_id"]]
        )

        max_positions = int(internship.get("max_positions", 5))

        if current_count >= max_positions:
            return jsonify({"success": False, "message": "Position limit reached"}), 400

        already = any(x["application_id"] == app_id for x in accepted)

        if not already:
            accepted.append(
                {
                    "id": str(uuid.uuid4()),
                    "application_id": updated_app["application_id"],
                    "internship_id": internship["internship_id"],
                    "company_id": internship["company_id"],
                    "student_id": updated_app["student_id"],
                    "student_name": updated_app["student_name"],
                    "company_name": internship["company_name"],
                    "title": internship["title"],
                    "accepted_at": datetime.now().isoformat(),
                }
            )

    # -------- REJECT LOGIC --------
    if status == "rejected":
        accepted = [x for x in accepted if x["application_id"] != app_id]

    # -------- SAVE DATA --------
    csv_handler.write_csv("data/applications.csv", apps)
    csv_handler.write_csv("data/accepted_applications.csv", accepted)

    return jsonify({"success": True})


@app.route("/api/student/accepted-internships")
def student_accepted():
    user = session_manager.get_current_user()

    if not user or user["role"] != "student":
        return jsonify({"success": False}), 403

    accepted = csv_handler.read_csv("data/accepted_applications.csv")

    my_data = [a for a in accepted if a["student_id"] == user["user"]["id"]]

    return jsonify({"success": True, "internships": my_data})


@app.route("/api/student/notifications")
def student_notifications():
    user = session_manager.get_current_user()

    if not user or user["role"] != "student":
        return jsonify({"success": False}), 403

    notes = csv_handler.read_csv("data/notifications.csv")

    my_notes = [n for n in notes if n["user_id"] == user["user"]["id"]]

    return jsonify({"success": True, "notifications": my_notes[::-1]})


@app.route("/api/company/view-cv/<filename>")
def view_cv(filename):
    user = session_manager.get_current_user()

    if not user or user["role"] != "company":
        return jsonify({"success": False}), 403

    # Prevent path traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        return jsonify({"success": False}), 400

    apps = csv_handler.read_csv("data/applications.csv")

    # Ensure CV belongs to company
    allowed = any(
        a["cv_file"] == filename and a["company_id"] == user["user"]["id"] for a in apps
    )

    if not allowed:
        return jsonify({"success": False, "message": "Unauthorized"}), 403

    path = os.path.join("cv_uploads", filename)

    if not os.path.exists(path):
        return jsonify({"success": False, "message": "File not found"}), 404

    return send_file(path, mimetype="application/pdf")


if __name__ == "__main__":
    init_csv_files()
    app.run(debug=True, port=5000)
