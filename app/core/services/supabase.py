import os

from supabase import create_client, Client

supabase_client: Client = create_client(
    os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY")
)
