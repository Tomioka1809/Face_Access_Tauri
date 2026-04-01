from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .config import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    user_code = Column(String(50), unique=True, index=True, nullable=False)
    password = Column(String(100), nullable=True) # Contraseña agregada
    
    # Aquí podríamos guardar una de dos cosas: 
    # 1. El path del archivo PNG en local
    # 2. Convertir tu ArcFace a un Vector y guardarlo (Para PGVector)
    # Por ahora mantendremos compatibilidad con tus PNGs locales:
    face_image_path = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    logs = relationship("AccessLog", back_populates="user")

class AccessLog(Base):
    __tablename__ = "access_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    access_status = Column(String(50)) # "Approved", "Denied"
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="logs")
