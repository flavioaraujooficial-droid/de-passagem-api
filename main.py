import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="De Passagem API")

# --- ROTA PASSAGEIRO (HOME) ---
@app.get("/", response_class=HTMLResponse)
def home():
    caminho = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Passageiro: index.html não encontrado</h1>"

# --- ROTA MOTORISTA ---
@app.get("/motorista", response_class=HTMLResponse)
def motorista():
    caminho = os.path.join(os.path.dirname(__file__), "motorista.html")
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Motorista: motorista.html não encontrado</h1>"

# --- ROTA ADMIN ---
@app.get("/admin", response_class=HTMLResponse)
def admin():
    caminho = os.path.join(os.path.dirname(__file__), "admin.html")
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Admin: admin.html não encontrado</h1>"
