"""
Run this ONCE to generate the values needed for a test staff account.
It does NOT touch your database - it just prints out a ready-to-paste
SQL INSERT statement, plus your TOTP secret so you can set up an
authenticator app.
"""
import uuid

import pyotp
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ---- EDIT THESE THREE VALUES FOR YOUR TEST ACCOUNT ----
USERNAME = "admin_sam"
PLAIN_PASSWORD = "AdminPass123!"
FULL_NAME = "Samuel Kariuki"
DEPARTMENT = "System Administration"
ROLE = "admin"
# --------------------------------------------------------

user_id = str(uuid.uuid4())
password_hash = pwd_context.hash(PLAIN_PASSWORD)
totp_secret = pyotp.random_base32()

print("=" * 70)
print("SAVE THIS INFO - you'll need it to log in:")
print("=" * 70)
print(f"Username:      {USERNAME}")
print(f"Password:      {PLAIN_PASSWORD}")
print(f"TOTP Secret:   {totp_secret}")
print()
print("To get a 6-digit login code right now, run:")
print(f'    python -c "import pyotp; print(pyotp.TOTP(\'{totp_secret}\').now())"')
print("=" * 70)
print()
print("PASTE AND RUN THIS IN PGADMIN (Query Tool, on sprms_db):")
print("-" * 70)
print(f"""
INSERT INTO staff_accounts (user_id, username, password_hash, totp_secret, full_name, department, role)
VALUES (
    '{user_id}',
    '{USERNAME}',
    '{password_hash}',
    '{totp_secret}',
    '{FULL_NAME}',
    '{DEPARTMENT}',
    '{ROLE}'
);
""")
print("-" * 70)