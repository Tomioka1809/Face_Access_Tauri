import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.database import models, config

# Crear todas las tablas en la base de datos de PostgreSQL
print("Configurando Tablas en la Base de Datos...")
models.Base.metadata.create_all(bind=config.engine)

app = FastAPI(title="Biometric Desktop API")

# Tauri React requiere permisos CORS para comunicarse con el servidor local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from core.api import stream
app.include_router(stream.router)

@app.get("/")
def home():
    return {"status": "Escuchando en el Sidecar de Python..."}

if __name__ == "__main__":
    print("Iniciando servidor FastAPI en http://localhost:8000 ...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
