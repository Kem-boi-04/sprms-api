"""
Admin dashboard endpoints - user management and audit trail.
"""
from fastapi import APIRouter, Depends, HTTPException
from psycopg import AsyncConnection
from app.core.auth import get_authenticated_db

router = APIRouter(prefix="/admin", tags=["admin"])

async def _ensure_is_admin(db: AsyncConnection):
    async with db.cursor() as cur:
        await cur.execute(
            "SELECT role FROM staff_accounts WHERE user_id = current_setting('app.current_user_id')::uuid"
        )
        row = await cur.fetchone()
    if row is None or row["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can access this")

@router.get("/users")
async def list_users(db: AsyncConnection = Depends(get_authenticated_db)):
    await _ensure_is_admin(db)
    async with db.cursor() as cur:
        await cur.execute(
            "SELECT user_id, username, full_name, department, role FROM staff_accounts ORDER BY username"
        )
        rows = await cur.fetchall()
    return {"count": len(rows), "users": rows}

@router.get("/audit-log")
async def get_audit_log(db: AsyncConnection = Depends(get_authenticated_db)):
    await _ensure_is_admin(db)
    async with db.cursor() as cur:
        await cur.execute(
            "SELECT log_id, event_timestamp, operator_id, action_type, current_hash "
            "FROM forensic_audit_log ORDER BY event_timestamp DESC LIMIT 50"
        )
        rows = await cur.fetchall()
    return {"count": len(rows), "logs": rows}