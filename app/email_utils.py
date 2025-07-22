import yagmail
import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

def send_email_report(to_email: str, subject: str, body: str, attachment_path: Optional[str] = None) -> bool:
    sender_email = os.getenv("EMAIL_SENDER")
    app_password = os.getenv("EMAIL_APP_PASSWORD")
    print(f"[DEBUG] EMAIL_SENDER: {sender_email!r}")
    print(f"[DEBUG] EMAIL_APP_PASSWORD is set: {bool(app_password)}")
    print(f"[DEBUG] Recipient: {to_email}, Subject: {subject}")
    print(f"[DEBUG] Attachment path: {attachment_path}")
    if not sender_email or not app_password:
        print("[ERROR] Missing EMAIL_SENDER or EMAIL_APP_PASSWORD in environment.")
        return False
    try:
        yag = yagmail.SMTP(sender_email, app_password)
        print("[DEBUG] Yagmail client initialized successfully.")
        yag.send(
            to=to_email,
            subject=subject,
            contents=body,
            attachments=[attachment_path] if attachment_path else None
        )
        print(f"[SUCCESS] Email report sent to {to_email}")
        return True
    except yagmail.YagAuthError as e:
        print(f"[ERROR] Email authentication failed. Details: {e}")
        return False
    except yagmail.YagConnectionError as e:
        print(f"[ERROR] Could not connect to email server: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error sending email: {e}")
        return False
