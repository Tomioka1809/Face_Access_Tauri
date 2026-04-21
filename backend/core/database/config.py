import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Asumimos conexión a localhost donde configuraste pacman postgresql
# Obtenemos el usuario activo (de la variable de entorno USER que Linux inyecta) para que coincida con createuser
USER = os.getenv("USER", "postgres")
DATABASE_URL = os.getenv("DATABASE_URL", f"postgresql://{USER}@localhost:5432/face_access_db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependencia para los Endpoints (FastAPI)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
