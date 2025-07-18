import yagmail
import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

def send_email_report(to_email: str, subject: str, body: str, attachment_path: Optional[str] = None) -> bool:
    sender_email = os.getenv("EMAIL_SENDER")
    app_password = os.getenv("EMAIL_APP_PASSWORD")
    if not sender_email or not app_password:
        print("Missing EMAIL_SENDER or EMAIL_APP_PASSWORD in environment.")
        return False
    try:
        yag = yagmail.SMTP(sender_email, app_password)
        yag.send(
            to=to_email,
            subject=subject,
            contents=body,
            attachments=[attachment_path] if attachment_path else None
        )
        print(f"Email report sent to {to_email}")
        return True
    except yagmail.YagAuthError:
        print("Email authentication failed.")
        return False
    except yagmail.YagConnectionError as e:
        print(f"Could not connect to email server: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error sending email: {e}")
        return False
