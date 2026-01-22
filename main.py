from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import sqlite3
import os

app = FastAPI()

# Modelos de datos
class ConfigObra(BaseModel):
    arancel: float
    modulo: float

class ChangePass(BaseModel):
    old_pass: str
    new_pass: str

# --- BASE DE DATOS ---
DB_PATH = "obras.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        # Tabla de configuración económica
        conn.execute("""
            CREATE TABLE IF NOT EXISTS configuracion (
                id INTEGER PRIMARY KEY, 
                arancel REAL, 
                modulo REAL
            )
        """)
        # Tabla de seguridad
        conn.execute("""
            CREATE TABLE IF NOT EXISTS seguridad (
                id INTEGER PRIMARY KEY, 
                password TEXT
            )
        """)
        # Valores iniciales si no existen
        conn.execute("INSERT OR IGNORE INTO configuracion (id, arancel, modulo) VALUES (1, 1320000, 1000)")
        conn.execute("INSERT OR IGNORE INTO seguridad (id, password) VALUES (1, '9dejulio')")
        conn.commit()

init_db()

# --- RUTAS DE API ---

@app.get("/api/config")
def get_config():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT arancel, modulo FROM configuracion WHERE id = 1").fetchone()
        return dict(row)

@app.post("/api/config")
def update_config(config: ConfigObra):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE configuracion SET arancel = ?, modulo = ? WHERE id = 1", 
                     (config.arancel, config.modulo))
        return {"status": "ok"}

@app.post("/api/login")
async def login(request: Request):
    data = await request.json()
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("SELECT password FROM seguridad WHERE id = 1").fetchone()
        if data.get("password") == row[0]:
            return {"auth": True}
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")

@app.post("/api/change-password")
def change_password(data: ChangePass):
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("SELECT password FROM seguridad WHERE id = 1").fetchone()
        if data.old_pass != row[0]:
            raise HTTPException(status_code=401, detail="La clave actual no es correcta")
        
        conn.execute("UPDATE seguridad SET password = ? WHERE id = 1", (data.new_pass,))
        return {"status": "Contraseña actualizada"}

# --- SERVIR FRONTEND ---
# Esto sirve todo lo que esté en la carpeta /static
app.mount("/", StaticFiles(directory="static", html=True), name="static")