from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from database import supabase

app = FastAPI(title="De Passagem API", version="1.0.0")

# Libera o acesso para o aplicativo mobile e web
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Estruturas de dados (Pydantic Models) ---
class SolicitarCorridaRequest(BaseModel):
    usuario_id: str
    origem_endereco: str
    origem_lat: float
    origem_lng: float
    destino_endereco: str
    destino_lat: float
    destino_lng: float
    distancia_km: float
    tipo_modalidade: str
    quantidade_paradas: int = 0

class FinalizarCorridaRequest(BaseModel):
    corrida_id: str
    motorista_id: str

class AvaliarCorridaRequest(BaseModel):
    corrida_id: str
    avaliador_id: str
    avaliado_id: str
    nota: int = Field(..., ge=1, le=5)
    comentario: str = None

class AprovarMotoristaRequest(BaseModel):
    motorista_id: str
    aprovado: bool

class AtualizarTarifasRequest(BaseModel):
    taxa_fixa_minima_app: float
    porcentagem_app_longa_distancia: float
    tarifa_km_base: float
    taxa_adicional_parada: float

class SalvarLocalFavoritoRequest(BaseModel):
    usuario_id: str
    nome_local: str
    endereco_completo: str
    latitude: float
    longitude: float

# --- Rota Inicial (Healthcheck da API) ---
@app.get("/")
def home():
    return {
        "status": "online",
        "app": "De Passagem API",
        "versao": "1.0.0"
    }

# --- Rotas do Passageiro e Motorista ---
@app.post("/corridas/solicitar")
def solicitar_corrida(dados: SolicitarCorridaRequest):
    config_res = supabase.table("configuracoes_sistema").select("*").limit(1).execute()
    config = config_res.data[0]
    
    taxa_fixa_app = float(config["taxa_fixa_minima_app"])
    tarifa_km_base = float(config["tarifa_km_base"])
    porcentagem_app = float(config["porcentagem_app_longa_distancia"]) / 100
    valor_por_parada = float(config["taxa_adicional_parada"])
    
    valor_bruto = (dados.distancia_km * tarifa_km_base) + (dados.quantidade_paradas * valor_por_parada)
    taxa_12 = valor_bruto * porcentagem_app
    taxa_plataforma = taxa_fixa_app if taxa_12 < taxa_fixa_app else taxa_12
    valor_liquido_motorista = valor_bruto - taxa_plataforma

    nova_corrida = {
        "usuario_id": dados.usuario_id,
        "tipo_modalidade": dados.tipo_modalidade,
        "quantidade_paradas": dados.quantidade_paradas,
        "origem_endereco": dados.origem_endereco,
        "origem_lat": dados.origem_lat,
        "origem_lng": dados.origem_lng,
        "destino_endereco": dados.destino_endereco,
        "destino_lat": dados.destino_lat,
        "destino_lng": dados.destino_lng,
        "distancia_calculada_km": dados.distancia_km,
        "valor_bruto": round(valor_bruto, 2),
        "taxa_plataforma": round(taxa_plataforma, 2),
        "valor_liquido_motorista": round(valor_liquido_motorista, 2),
        "status": "solicitado"
    }

    resposta = supabase.table("corridas").insert(nova_corrida).execute()
    return {"mensagem": "Corrida solicitada com sucesso!", "detalhes": resposta.data[0]}

@app.post("/corridas/finalizar")
def finalizar_corrida(dados: FinalizarCorridaRequest):
    supabase.table("corridas").update({"status": "finalizada"}).eq("id", dados.corrida_id).execute()
    supabase.table("motoristas").update({"status": "online"}).eq("id", dados.motorista_id).execute()
    return {"mensagem": "Corrida finalizada com sucesso!", "corrida_id": dados.corrida_id}

@app.post("/corridas/avaliar")
def avaliar_corrida(dados: AvaliarCorridaRequest):
    nova_avaliacao = {
        "corrida_id": dados.corrida_id,
        "avaliador_id": dados.avaliador_id,
        "avaliado_id": dados.avaliado_id,
        "nota": dados.nota,
        "comentario": dados.comentario
    }
    resposta = supabase.table("avaliacoes").insert(nova_avaliacao).execute()
    return {"mensagem": "Avaliação registrada com sucesso!", "detalhes": resposta.data[0]}

# --- ROTAS DE LOCAIS FAVORITOS (Resiliência de GPS) ---

@app.post("/locais-favoritos/salvar")
def salvar_local_favorito(dados: SalvarLocalFavoritoRequest):
    novo_local = {
        "usuario_id": dados.usuario_id,
        "nome_local": dados.nome_local,
        "endereco_completo": dados.endereco_completo,
        "latitude": dados.latitude,
        "longitude": dados.longitude
    }
    resposta = supabase.table("locais_favoritos").insert(novo_local).execute()
    return {"mensagem": "Local favorito salvo com sucesso!", "detalhes": resposta.data[0]}

@app.get("/locais-favoritos/{usuario_id}")
def listar_locais_favoritos(usuario_id: str):
    resposta = supabase.table("locais_favoritos").select("*").eq("usuario_id", usuario_id).execute()
    return {"locais": resposta.data}

# --- ROTAS ADMINISTRATIVAS (Painel do Gestor) ---

@app.get("/admin/dashboard")
def resumo_dashboard():
    corridas = supabase.table("corridas").select("*").execute().data
    motoristas = supabase.table("motoristas").select("*").execute().data
    
    total_corridas = len(corridas)
    faturamento_bruto = sum(float(c.get("valor_bruto", 0)) for c in corridas if c.get("status") == "finalizada")
    receita_plataforma = sum(float(c.get("taxa_plataforma", 0)) for c in corridas if c.get("status") == "finalizada")
    motoristas_online = len([m for m in motoristas if m.get("status") == "online"])

    return {
        "total_corridas": total_corridas,
        "faturamento_bruto": round(faturamento_bruto, 2),
        "receita_plataforma": round(receita_plataforma, 2),
        "motoristas_online": motoristas_online
    }

@app.get("/admin/motoristas")
def listar_motoristas():
    resposta = supabase.table("motoristas").select("*").execute()
    return {"motoristas": resposta.data}

@app.post("/admin/motoristas/aprovar")
def aprovar_motorista(dados: AprovarMotoristaRequest):
    novo_status = "online" if dados.aprovado else "bloqueado"
    resposta = supabase.table("motoristas").update({"status": novo_status}).eq("id", dados.motorista_id).execute()
    return {"mensagem": f"Status do motorista atualizado para {novo_status}!", "detalhes": resposta.data}

@app.post("/admin/tarifas/atualizar")
def atualizar_tarifas(dados: AtualizarTarifasRequest):
    novas_config = {
        "taxa_fixa_minima_app": dados.taxa_fixa_minima_app,
        "porcentagem_app_longa_distancia": dados.porcentagem_app_longa_distancia,
        "tarifa_km_base": dados.tarifa_km_base,
        "taxa_adicional_parada": dados.taxa_adicional_parada
    }
    config_id = supabase.table("configuracoes_sistema").select("id").limit(1).execute().data[0]["id"]
    resposta = supabase.table("configuracoes_sistema").update(novas_config).eq("id", config_id).execute()
    return {"mensagem": "Tarifas atualizadas com sucesso!", "configuracoes": resposta.data[0]}
