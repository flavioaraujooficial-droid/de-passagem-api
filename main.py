from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

# Estruturas de dados das requisições
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
    nota: int = Field(..., ge=1, le=5)  # Nota obrigatória entre 1 e 5
    comentario: str = None

@app.get("/")
def status_api():
    return {"status": "online", "sistema": "De Passagem", "cidade": "Alagoinhas/BA"}

@app.post("/corridas/solicitar")
def solicitar_corrida(dados: SolicitarCorridaRequest):
    # Busca configurações atualizadas no Supabase
    config_res = supabase.table("configuracoes_sistema").select("*").limit(1).execute()
    config = config_res.data[0]
    
    taxa_fixa_app = float(config["taxa_fixa_minima_app"])
    tarifa_km_base = float(config["tarifa_km_base"])
    porcentagem_app = float(config["porcentagem_app_longa_distancia"]) / 100
    valor_por_parada = float(config["taxa_adicional_parada"])
    
    # Cálculo bruto do valor da corrida
    valor_bruto = (dados.distancia_km * tarifa_km_base) + (dados.quantidade_paradas * valor_por_parada)
    
    # Aplica a regra de taxa mista da plataforma (R$ 2,00 ou 12%)
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
    # 1. Encerra a corrida no banco de dados
    corrida_res = supabase.table("corridas").update({
        "status": "finalizada"
    }).eq("id", dados.corrida_id).execute()

    # 2. Libera o motorista para ficar 'online' novamente
    supabase.table("motoristas").update({
        "status": "online"
    }).eq("id", dados.motorista_id).execute()

    return {
        "mensagem": "Corrida finalizada com sucesso!",
        "corrida_id": dados.corrida_id,
        "proximo_passo": "abrir_tela_avaliacao"
    }

@app.post("/corridas/avaliar")
def avaliar_corrida(dados: AvaliarCorridaRequest):
    # 1. Registra a avaliação na tabela 'avaliacoes'
    nova_avaliacao = {
        "corrida_id": dados.corrida_id,
        "avaliador_id": dados.avaliador_id,
        "avaliado_id": dados.avaliado_id,
        "nota": dados.nota,
        "comentario": dados.comentario
    }
    
    resposta = supabase.table("avaliacoes").insert(nova_avaliacao).execute()
    
    return {
        "mensagem": "Avaliação registrada com sucesso!",
        "detalhes": resposta.data[0]
    }
