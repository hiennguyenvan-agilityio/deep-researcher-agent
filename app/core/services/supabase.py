import os

from supabase import create_client

_supabase_client = None


def get_instance():
    global _supabase_client

    if _supabase_client is None:
        _supabase_client = create_client(
            os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY")
        )

    return _supabase_client
