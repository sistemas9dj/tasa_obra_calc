from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import sqlite3
import os

app = FastAPI(root_path="/tasa_obra_calc")





# Modelos de datos
class ConfigObra(BaseModel):
    arancel: float
    modulo: float
    carpeta: float

class ChangePass(BaseModel):
    old_pass: str
    new_pass: str

class ObraConstructiva(BaseModel):
    propietario: str
    tipo_tramite: str
    tipo_obra: str
    superficie: float
    factor: float
    monto_obra: float
    tasa_base: float
    desc_antiguedad: float
    desc_servicios: float
    tasa_neta: float
    carpeta: float
    total: float

# --- BASE DE DATOS ---



DB_PATH = "/obras.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        # Tabla de configuración económica
        conn.execute("""
            CREATE TABLE IF NOT EXISTS configuracion (
                id INTEGER PRIMARY KEY, 
                arancel REAL, 
                modulo REAL,
                carpeta REAL
            )
        """)
        # Tabla de seguridad
        conn.execute("""
            CREATE TABLE IF NOT EXISTS seguridad (
                id INTEGER PRIMARY KEY, 
                password TEXT
            )
        """)
        # Tabla de obras (nuevo)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS obras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                propietario TEXT,
                tipo_tramite TEXT,
                tipo_obra TEXT,
                superficie REAL,
                factor REAL,
                monto_obra REAL,
                tasa_base REAL,
                desc_antiguedad REAL,
                desc_servicios REAL,
                tasa_neta REAL,
                carpeta REAL,
                total REAL,
                fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Valores iniciales si no existen
        conn.execute("INSERT OR IGNORE INTO configuracion (id, arancel, modulo, carpeta) VALUES (1, 1320000, 1000, 7733)")
        conn.execute("INSERT OR IGNORE INTO seguridad (id, password) VALUES (1, '9dejulio')")
        conn.commit()

@app.on_event("startup")
def startup():
    print("🚀 Startup ejecutado")
    print("DB_PATH:", DB_PATH)
    init_db()


# --- RUTAS DE API ---

@app.get("/api/config")
def get_config():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT arancel, modulo, carpeta FROM configuracion WHERE id = 1").fetchone()
        return dict(row)

@app.post("/api/config")
def update_config(config: ConfigObra):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE configuracion SET arancel = ?, modulo = ?, carpeta = ? WHERE id = 1", 
                     (config.arancel, config.modulo, config.carpeta))
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

# --- ENDPOINTS PARA OBRAS MÚLTIPLES ---

@app.post("/api/obras")
def agregar_obra(obra: ObraConstructiva):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """INSERT INTO obras (propietario, tipo_tramite, tipo_obra, superficie, factor, monto_obra, 
               tasa_base, desc_antiguedad, desc_servicios, tasa_neta, carpeta, total) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (obra.propietario, obra.tipo_tramite, obra.tipo_obra, obra.superficie, obra.factor, 
             obra.monto_obra, obra.tasa_base, obra.desc_antiguedad, obra.desc_servicios, 
             obra.tasa_neta, obra.carpeta, obra.total)
        )
        conn.commit()
        return {"status": "ok", "message": "Obra agregada"}

@app.get("/api/obras")
def obtener_obras():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""SELECT id, propietario, tipo_tramite, tipo_obra, superficie, factor, 
                             monto_obra, tasa_base, desc_antiguedad, desc_servicios, tasa_neta, 
                             carpeta, total FROM obras ORDER BY id DESC""").fetchall()
        return [dict(row) for row in rows]

@app.delete("/api/obras/{obra_id}")
def eliminar_obra(obra_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM obras WHERE id = ?", (obra_id,))
        conn.commit()
        return {"status": "ok", "message": "Obra eliminada"}

@app.get("/api/obras/total")
def obtener_total_obras():
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("SELECT SUM(total) as total FROM obras").fetchone()
        total = row[0] if row[0] else 0
        return {"total": total}

# --- SERVIR FRONTEND ---
# Esto sirve todo lo que esté en la carpeta /static
app.mount(
    "/",
    StaticFiles(directory="static", html=True),
    name="static"
)