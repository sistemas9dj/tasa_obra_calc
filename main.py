from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import sqlite3

app = FastAPI()

# Clase para validar los datos que entran
class ConfigObra(BaseModel):
    arancel: float
    modulo: float

# Inicializar Base de Datos
def init_db():
    with sqlite3.connect("obras.db") as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS configuracion (
                id INTEGER PRIMARY KEY, 
                arancel REAL, 
                modulo REAL
            )
        """)
        conn.execute("INSERT OR IGNORE INTO configuracion (id, arancel, modulo) VALUES (1, 1320000, 1000)")

init_db()

@app.get("/api/config")
def get_config():
    with sqlite3.connect("obras.db") as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT arancel, modulo FROM configuracion WHERE id = 1").fetchone()
        return dict(row)

@app.post("/api/config")
def update_config(config: ConfigObra):
    with sqlite3.connect("obras.db") as conn:
        conn.execute("UPDATE configuracion SET arancel = ?, modulo = ? WHERE id = 1", 
                     (config.arancel, config.modulo))
        return {"status": "Actualizado correctamente"}

# Servir el HTML (Debe ir al final para no pisar las rutas API)
app.mount("/", StaticFiles(directory="static", html=True), name="static")