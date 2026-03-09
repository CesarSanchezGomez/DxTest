from supabase import create_client, Client
from backend.config import get_settings

settings = get_settings()

_client: Client = create_client(settings.supabase_url, settings.supabase_key)


def get_supabase_client() -> Client:
    return _client
