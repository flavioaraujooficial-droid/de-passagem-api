import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI(title="De Passagem API - Mobilidade Urbana")

# Armazenamento em memória do estado atual da corrida
corrida_ativa = {}

class SolicitarCorrida(BaseModel):
    passageiro: str = "Passageiro"
    origem: str
    destino: str

# --- ROTAS DE PÁGINAS (HTML) ---

@app.get("/", response_class=HTMLResponse)
def home():
    caminho = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Passageiro: index.html não encontrado</h1>"

@app.get("/motorista", response_class=HTMLResponse)
def motorista():
    caminho = os.path.join(os.path.dirname(__file__), "motorista.html")
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Motorista: motorista.html não encontrado</h1>"

@app.get("/admin", response_class=HTMLResponse)
def admin():
    caminho = os.path.join(os.path.dirname(__file__), "admin.html")
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Admin: admin.html não encontrado</h1>"


# --- API OPERACIONAL DE CORRIDAS ---

@app.post("/corridas/solicitar")
def solicitar_corrida(dados: SolicitarCorrida):
    global corrida_ativa
    corrida_ativa = {
        "passageiro": dados.passageiro,
        "origem": dados.origem,
        "destino": dados.destino,
        "status": "pendente"
    }
    return {"status": "sucesso", "corrida": corrida_ativa}

@app.get("/corridas/pendentes")
def corridas_pendentes():
    global corrida_ativa
    return corrida_ativa

@app.post("/corridas/aceitar")
def aceitar_corrida():
    global corrida_ativa
    if corrida_ativa:
        corrida_ativa["status"] = "aceita"
    return {"status": "aceita"}

@app.post("/corridas/finalizar")
def finalizar_corrida():
    global corrida_ativa
    corrida_ativa = {}
    return {"status": "finalizada"}
