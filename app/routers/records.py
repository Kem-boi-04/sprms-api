"""
This router proves the entire point of your Section 4.3 architecture:
that Row-Level Security filters data automatically, even when the
request comes through the API instead of pgAdmin's Query Tool.

GET /records/mine will ONLY ever return rows belonging to whoever's
JWT token was sent - not because this code filters them, but because
get_authenticated_db() already ran:
    SET app.current_user_id = '<their uuid>'
before this function's query even executes. The WHERE-clause-like
filtering happens inside Postgres itself, via the RLS policies you
wrote in 04_enable_rls.sql.
"""
from fastapi import APIRouter, Depends
from psycopg import AsyncConnection

from app.core.auth import get_authenticated_db
from app.core.config import settings

router = APIRouter(prefix="/records", tags=["records"])


@router.get("/mine")
async def get_my_records(db: AsyncConnection = Depends(get_authenticated_db)):
    """
    Returns medical_records visible to the currently authenticated user.
    Notice: no patient_id filter appears anywhere in this query below.
    That's intentional - Postgres RLS is doing the filtering, not this code.
    """
    async with db.cursor() as cur:
        await cur.execute(
            """
            SELECT
                record_id,
                patient_id,
                provider_id,
                pgp_sym_decrypt(clinical_notes_enc, %s) AS clinical_notes,
                icd10_code,
                timestamp
            FROM medical_records
            ORDER BY timestamp DESC
            """,
            (settings.pgcrypto_key,),
        )
        rows = await cur.fetchall()

    return {"count": len(rows), "records": rows}
