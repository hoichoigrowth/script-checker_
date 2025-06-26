import json
import os

STORAGE_FILE = "storage.json"

def login_user(email):
    return "@hoichoi.tv" in email.lower()

def is_admin(email):
    return email.lower() == "admin@hoichoi.tv"

def save_login_email(email):
    email = email.lower()
    if not os.path.exists(STORAGE_FILE):
        with open(STORAGE_FILE, "w") as f:
            json.dump([], f)

    try:
        with open(STORAGE_FILE, "r") as f:
            emails = json.load(f)
    except json.JSONDecodeError:
        emails = []

    if email not in emails:
        emails.append(email)
        with open(STORAGE_FILE, "w") as f:
            json.dump(emails, f, indent=2)
