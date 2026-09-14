from supabase import create_client, Client
from app.config import settings

def get_supabase() -> Client:
    """Returns a Supabase client using settings from config.py.
    Prefers service key for backend operations to bypass RLS restrictions."""
    key = settings.supabase_service_key or settings.supabase_key
    return create_client(settings.supabase_url, key)
