# Usa una imagen oficial de Python 3.12 (slim para que pese menos)
FROM python:3.12-slim

# Instalar dependencias del sistema necesarias para OpenCV, Mediapipe, dlib, etc.
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Configura el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar el archivo de requerimientos
COPY requirements.txt .

# Instalar las librerias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del codigo de tu app
COPY . .

# Expone el puerto que usa FastAPI
EXPOSE 8000

# Comando para iniciar la aplicacion
CMD ["python", "main.py"]
