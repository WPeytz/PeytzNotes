"""Shared, database-backed hourly budget for costly public demo operations."""

import hashlib
import os
import time

from fastapi import HTTPException, Request
from sqlalchemy import text

from app.models.database import async_session


async def check_demo_rate_limit(request: Request) -> None:
    limit = int(os.getenv("PEYTZNOTES_DEMO_HOURLY_LIMIT", "30"))
    hour_bucket = int(time.time() // 3600)
    address = request.client.host if request.client else "unknown"
    client_key = hashlib.sha256(address.encode("utf-8")).hexdigest()

    async with async_session() as session:
        result = await session.execute(text("""
            INSERT INTO demo_rate_limits (client_key, hour_bucket, request_count)
            VALUES (:client_key, :hour_bucket, 1)
            ON CONFLICT (client_key) DO UPDATE SET
                hour_bucket = EXCLUDED.hour_bucket,
                request_count = CASE
                    WHEN demo_rate_limits.hour_bucket = EXCLUDED.hour_bucket
                    THEN demo_rate_limits.request_count + 1
                    ELSE 1
                END
            RETURNING request_count
        """), {"client_key": client_key, "hour_bucket": hour_bucket})
        count = result.scalar_one()
        await session.commit()

    if count > limit:
        raise HTTPException(
            status_code=429,
            detail="Demo limit reached. Please try again later.",
            headers={"Retry-After": str(3600 - int(time.time() % 3600))},
        )
