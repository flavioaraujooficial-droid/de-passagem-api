import os
from supabase import create_client, Client

# Pega a URL e a KEY das variáveis de ambiente da Vercel
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Conexão segura e blindada contra Erro 500
if SUPABASE_URL and SUPABASE_KEY and SUPABASE_KEY != "COLE_SUA_SERVICE_ROLE_KEY_AQUI":
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Erro ao conectar no Supabase: {e}")
        supabase = None
else:
    print("Aviso: Variáveis do Supabase não configuradas ou usando chave padrão.")
    supabase = None
