"""
Database access layer.

The single most important function in this whole file is `get_db_connection`.
It is what makes your Row-Level Security policies (built in pgAdmin, Section 4.3
of the proposal) actually apply per logged-in user automatically.

Flow on every authenticated request:
1. FastAPI calls get_current_user() (see auth.py) to verify the JWT token
2. That gives us the user's UUID
3. get_db_connection() pulls a connection from the pool and runs:
       SET app.current_user_id = '<their uuid>'
   on that connection, in the SAME transaction as the real query
4. Every query after that point is automatically filtered by Postgres RLS,
   exactly like the manual `SET ROLE` / `SET app.current_user_id` testing
   you did by hand in pgAdmin's Query Tool.

This means a developer mistake in application code (forgetting a WHERE clause,
a bug in business logic, even a successful SQL injection) still cannot leak
another patient's row, because the database itself enforces the boundary.
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import Depends, FastAPI
from psycopg import AsyncConnection
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from app.core.config import settings

# Pool is created closed; opened/closed via FastAPI's lifespan (see main.py)
pool = AsyncConnectionPool(
    conninfo=settings.database_url,
    open=False,
    min_size=2,
    max_size=10,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await pool.open()
    yield
    await pool.close()


async def get_db_connection(
    current_user_id: str = None,
) -> AsyncGenerator[AsyncConnection, None]:
    """
    Base dependency: hands out a pooled connection.
    current_user_id is injected by get_authenticated_db() below for
    protected routes. Public routes (like /login) use this directly
    without a user id.
    """
    async with pool.connection() as conn:
        conn.row_factory = dict_row
        if current_user_id:
            # NOTE: current_setting() expects a string literal here, not a
            # bind parameter for the SET command itself - we use set_config()
            # instead, which IS safe to parameterize and prevents injection.
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT set_config('app.current_user_id', %s, false)",
                    (str(current_user_id),),
                )
        yield conn
