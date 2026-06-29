"""Supabase client singleton. Import `db` everywhere."""
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

_SUPABASE_URL = os.environ["SUPABASE_URL"]
_SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]  # service key: bypasses RLS, backend-only

db: Client = create_client(_SUPABASE_URL, _SUPABASE_KEY)


def get_db() -> Client:
    return db
