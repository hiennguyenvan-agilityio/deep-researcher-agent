from fastapi import logger
from supabase_auth import User

from app.core.services.supabase import supabase_client


async def get_user(token: str | None) -> User | None:
    if not token:
        return None

    token = token.replace("Bearer ", "")

    try:
        response = supabase_client.auth.get_user(token)

        return response.user
    except Exception as e:
        logger.warning("Failed to get Supabase user: %s", e)

        return None
