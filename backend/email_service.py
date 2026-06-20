import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load .env variables
load_dotenv()


class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.sender_email = os.getenv('SMTP_USERNAME')
        self.sender_password = os.getenv('SMTP_PASSWORD')

        self.use_mock = not all([self.sender_email, self.sender_password])

        if self.use_mock:
            print("⚠ EmailService running in MOCK mode.")


    # --------------------------------------------------
    # Email Verification
    # --------------------------------------------------
    def send_verification_email(self, recipient_email, recipient_name, otp):
        subject = "VTernship - Verify Your Email"

        html_content = f"""
        <html>
        <body style="font-family: Arial;">
            <h2>Hello {recipient_name},</h2>
            <p>Please verify your email using this OTP:</p>
            <h1 style="letter-spacing:5px;">{otp}</h1>
            <p>This OTP expires in 15 minutes.</p>
            <br>
            <p>VTernship Team</p>
        </body>
        </html>
        """

        self._send_email(recipient_email, subject, html_content)

    # --------------------------------------------------
    # Password Reset
    # --------------------------------------------------
    def send_password_reset_email(self, recipient_email, otp):
        subject = "VTernship - Password Reset"

        html_content = f"""
        <html>
        <body style="font-family: Arial;">
            <h2>Password Reset Request</h2>
            <p>Use the OTP below to reset your password:</p>
            <h1 style="letter-spacing:5px;">{otp}</h1>
            <p>This OTP expires in 15 minutes.</p>
        </body>
        </html>
        """

        self._send_email(recipient_email, subject, html_content)

    # --------------------------------------------------
    # Company Approval
    # --------------------------------------------------
    def send_approval_email(self, recipient_email, company_name):
        subject = "VTernship - Account Approved"

        html_content = f"""
        <html>
        <body style="font-family: Arial;">
            <h2>Account Approved!</h2>
            <p>Dear {company_name},</p>
            <p>Your company account has been approved.</p>
            <p>You can now login and post internships.</p>
            <br>
            <p>VTernship Team</p>
        </body>
        </html>
        """

        self._send_email(recipient_email, subject, html_content)

    # --------------------------------------------------
    # SMTP Sender
    # --------------------------------------------------
    def _send_email(self, recipient_email, subject, html_content):
        if self.use_mock:
            print(f"\n[MOCK EMAIL]")
            print(f"To: {recipient_email}")
            print(f"Subject: {subject}")
            print(f"Content Preview: {html_content[:120]}...\n")
            return

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.sender_email
            msg["To"] = recipient_email

            plain_text = "Please view this email in HTML mode."
            msg.attach(MIMEText(plain_text, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)

            print(f"✅ Email sent to {recipient_email}")

        except Exception as e:
            print("❌ Email sending failed:", e)
            print("[Fallback] Printing email instead.\n")
            print(f"To: {recipient_email}")
            print(f"Subject: {subject}")
