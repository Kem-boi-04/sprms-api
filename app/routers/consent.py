"""
Patient consent management endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from psycopg import AsyncConnection
from pydantic import BaseModel
from app.core.auth import get_authenticated_db

router = APIRouter(prefix="/consent", tags=["consent"])

DEPARTMENTS = [
    "General Outpatient",
    "Pharmacy",
    "Emergency Room",
    "Cardiology",
    "Laboratory",
    "Radiology",
]

class ConsentUpdate(BaseModel):
    department: str
    allowed: bool

async def _ensure_is_patient(db: AsyncConnection):
    """Raises 403 if the currently authenticated user is not a patient."""
    async with db.cursor() as cur:
        await cur.execute(
            "SELECT role FROM staff_accounts WHERE user_id = current_setting('app.current_user_id')::uuid"
        )
        row = await cur.fetchone()
    if row is None or row["role"] != "patient":
        raise HTTPException(status_code=403, detail="Only patients can access consent settings")
@router.get("/my-settings")
async def get_my_consent(db: AsyncConnection = Depends(get_authenticated_db)):
    await _ensure_is_patient(db)
    async with db.cursor() as cur:
        await cur.execute(
            "SELECT target_dept, access_status FROM consent_toggle_settings "
            "WHERE patient_id = current_setting('app.current_user_id')::uuid"
        )
        rows = await cur.fetchall()
    existing = {row["target_dept"]: row["access_status"] for row in rows}
    result = []
    for dept in DEPARTMENTS:
        result.append({
            "department": dept,
            "allowed": existing.get(dept, False)
        })
    return result

@router.post("/update")
async def update_consent(
    update: ConsentUpdate,
    db: AsyncConnection = Depends(get_authenticated_db)
):
    await _ensure_is_patient(db)
    if update.department not in DEPARTMENTS:
        raise HTTPException(status_code=400, detail="Unknown department")
    async with db.cursor() as cur:
        await cur.execute("""
            INSERT INTO consent_toggle_settings (patient_id, target_dept, access_status, updated_at)
            VALUES (
                current_setting('app.current_user_id')::uuid,
                %s, %s, NOW()
            )
            ON CONFLICT (patient_id, target_dept)
            DO UPDATE SET access_status = EXCLUDED.access_status, updated_at = NOW()
        """, (update.department, update.allowed))
    await db.commit()
    return {"department": update.department, "allowed": update.allowed}