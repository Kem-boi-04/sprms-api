"""
Patient consent management endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from psycopg import AsyncConnection
from pydantic import BaseModel
from app.core.auth import get_authenticated_db
from app.core.config import settings

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

@router.get("/my-patients")
async def get_my_patients(db: AsyncConnection = Depends(get_authenticated_db)):
    """
    Returns patients who have granted the currently logged-in clinician
    active (non-expired) access, via consent_ledger.
    """
    async with db.cursor() as cur:
        await cur.execute(
            """
            SELECT
                p.patient_id,
                pgp_sym_decrypt(p.full_name_enc, %s) AS full_name,
                pgp_sym_decrypt(p.national_id_enc, %s) AS national_id,
                cl.permitted_department,
                cl.expiry_timestamp
            FROM consent_ledger cl
            JOIN patients p ON p.patient_id = cl.patient_id
            WHERE cl.accessor_id = current_setting('app.current_user_id')::uuid
              AND cl.expiry_timestamp > NOW()
            ORDER BY cl.expiry_timestamp ASC
            """,
            (settings.pgcrypto_key, settings.pgcrypto_key),
        )
        rows = await cur.fetchall()
    return {"count": len(rows), "patients": rows}

@router.get("/my-grants")
async def get_my_grants(db: AsyncConnection = Depends(get_authenticated_db)):
    """
    Returns clinicians who currently have active (non-expired) access
    to the logged-in patient's records, via consent_ledger.
    """
    async with db.cursor() as cur:
        await cur.execute(
            """
            SELECT
                cl.policy_id,
                sa.full_name AS doctor_name,
                cl.permitted_department,
                cl.expiry_timestamp
            FROM consent_ledger cl
            JOIN staff_accounts sa ON sa.user_id = cl.accessor_id
            WHERE cl.patient_id = current_setting('app.current_user_id')::uuid
              AND cl.expiry_timestamp > NOW()
            ORDER BY cl.expiry_timestamp ASC
            """
        )
        rows = await cur.fetchall()
    return {"count": len(rows), "grants": rows}