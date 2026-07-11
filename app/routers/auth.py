"""
Login endpoint - wired to the real staff_accounts table.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordRequestForm
from psycopg import AsyncConnection

from app.core.auth import create_access_token, verify_password, verify_totp
from app.core.database import get_db_connection

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    totp_code: str = Form(...),
    db: AsyncConnection = Depends(get_db_connection),
):
    async with db.cursor() as cur:
        await cur.execute(
            "SELECT user_id, password_hash, totp_secret "
            "FROM staff_accounts WHERE username = %s",
            (form_data.username,),
        )
        user = await cur.fetchone()

    if user is None or not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if not totp_code or not verify_totp(user["totp_secret"], totp_code):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing authentication code",
        )

    token = create_access_token(user_id=str(user["user_id"]))
    return {"access_token": token, "token_type": "bearer"}