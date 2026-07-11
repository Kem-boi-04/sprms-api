# SPRMS API — Phase 3 Starter Scaffold

This is the starting skeleton for your Phase 3 (Weeks 9–12) API Gateway layer.
It is NOT a finished login system — see "What's stubbed" below.

## What this proves

The core security pattern from your proposal: **the database enforces access
control, not the application code.** Specifically:

- `app/core/database.py` → `get_db_connection()` runs
  `SET app.current_user_id = '<uuid>'` on every authenticated request,
  before any query runs.
- `app/routers/records.py` → `GET /records/mine` queries `medical_records`
  with **no patient_id filter written anywhere in the Python code**. The
  filtering happens entirely inside Postgres via the RLS policies you
  built and tested in pgAdmin (`04_enable_rls.sql`).

This is the same mechanism you tested manually with `SET ROLE` /
`SET app.current_user_id` in the Query Tool — just automated per-request.

## Setup

```bash
# 1. Create a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy the env template and fill in real values
cp .env.example .env
# edit .env: set DATABASE_URL, JWT_SECRET_KEY, PGCRYPTO_KEY

# 4. Run the server
uvicorn app.main:app --reload
```

Then open **http://127.0.0.1:8000/docs** — FastAPI's auto-generated
interactive API explorer. You can test endpoints directly from the browser.

## What's stubbed (and needs your work next)

**`app/routers/auth.py` — the `/auth/login` endpoint is NOT wired to a real
accounts table.** Your current schema (Table 4.1) has no table for staff
login credentials (username, password_hash, totp_secret). Before login can
actually work, you need to:

1. Design and create a `staff_accounts` (or similar) table in pgAdmin —
   columns roughly: `user_id UUID`, `username VARCHAR`, `password_hash VARCHAR`,
   `totp_secret VARCHAR`, `role VARCHAR`
2. Write a small Python script (or manual pgAdmin insert) to create a test
   account — you'll need `hash_password()` from `app/core/auth.py` to
   generate the hash, and `pyotp.random_base32()` to generate a TOTP secret
3. Uncomment and adapt the TODO block in `app/routers/auth.py` to query that
   real table

**Patient login** is a separate question from staff login — your `patients`
table already exists, but you'll want to decide whether patients log in with
the same mechanism or a separate flow. Worth deciding before building further.

## Testing the RLS-through-API proof (once login works)

1. Log in via `/docs` → `POST /auth/login` → copy the returned token
2. Click "Authorize" in the Swagger UI, paste the token
3. Call `GET /records/mine`
4. Compare against logging in as a different test user — confirm each
   only ever sees their own (or consented) records, exactly like your
   manual pgAdmin RLS test, but now proven through the real API path.
