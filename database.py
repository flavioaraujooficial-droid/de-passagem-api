import os
from supabase import create_client, Client

# Busca a URL e a Chave das variáveis de ambiente
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://cwtnpzlboovnoznybeh.supabase.co")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "COLE_SUA_SERVICE_ROLE_KEY_AQUI")

# Cria a conexão oficial com o banco
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
