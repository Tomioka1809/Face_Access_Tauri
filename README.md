# Face Access Tauri - Sistema de Control de Acceso Facial

Este proyecto integra una interfaz gráfica de escritorio construida con **Tauri + React/Vite** junto con un backend inteligente construido en **Python (FastAPI)** y una base de datos **PostgreSQL**.

---

## 🏗️ Arquitectura y Estructura del Proyecto

El proyecto está diseñado siguiendo una arquitectura de separación de responsabilidades limpia y modularizada. En la raíz del proyecto encontrarás las siguientes carpetas principales:

### `1. backend/` (Lógica del Servidor y Base de Datos)
Contiene todo el código de Python encargado de procesar la lógica de negocio, la inteligencia artificial (procesamiento facial) y la comunicación con la base de datos.
*   **`Dockerfile` / `docker-compose.yml`**: Configuración para levantar el backend y la base de datos PostgreSQL en contenedores aislados.
*   **`core/api/`**: Los endpoints (rutas) de FastAPI.
*   **`core/database/`**: Modelos de SQLAlchemy y configuración de conexión. (Toda la interacción con la base de datos vive aquí).
*   **`requirements.txt`**: Dependencias de Python necesarias.

### `2. frontend/` (Interfaz de Usuario y App Nativa)
Contiene todo el código responsable de lo que ve el usuario final y la compilación de la aplicación de escritorio.
*   **`src/`**: El código fuente de React (componentes, estilos, lógica de UI).
*   **`src-tauri/`**: El núcleo de Tauri escrito en **Rust**. Actúa como el puente entre tu frontend web y las capacidades nativas de tu sistema operativo (ventanas, cámara, archivos locales).
*   **`package.json` / `vite.config.js`**: Configuraciones del servidor de desarrollo web y dependencias de NPM.

---

## 🚀 Cómo Iniciar el Proyecto

Para tener el sistema completo funcionando, necesitas levantar tanto el entorno de backend como la aplicación de escritorio.

### Paso 1: Levantar el Backend y la Base de Datos
El backend está "dockerizado" para que no tengas que instalar la base de datos ni librerías complejas manualmente.

1. Abre una terminal en la **raíz del proyecto** (`Face_Access_Tauri`).
2. Ejecuta el siguiente comando para levantar los servicios en segundo plano:
   ```bash
   docker compose up -d
   ```
*(Esto levantará el contenedor de Postgres y el contenedor de FastAPI).*

### Paso 2: Lanzar la Aplicación de Escritorio (Tauri)
El frontend web necesita compilarse y envolverse en la ventana nativa de Tauri.

1. Abre una **nueva terminal** (o usa otra pestaña).
2. Entra a la carpeta del frontend:
   ```bash
   cd frontend
   ```
3. Ejecuta el servidor de desarrollo de Tauri:
   ```bash
   npm run tauri dev
   ```
*(La primera vez puede tardar un poco mientras Rust compila las dependencias).*

---

## 🛠️ Historial: Cómo se reorganizó este proyecto (Paso a Paso)

Originalmente, este proyecto tenía los archivos del frontend y Tauri mezclados en la raíz junto con el backend. Para lograr esta arquitectura limpia, seguimos este proceso:

### 1. Creación de Carpetas y Renombrado
Primero, se ordenó la raíz creando contenedores lógicos para cada parte del sistema:
```bash
# Renombrar el backend para que el nombre sea más limpio
mv backend-python backend

# Crear la carpeta contenedora del frontend
mkdir frontend
```

### 2. Migración del Frontend
Se movieron todos los archivos relacionados con la web (React, Vite, Tailwind) a su nueva casa:
```bash
mv src public index.html package.json package-lock.json vite.config.js tailwind.config.js postcss.config.js node_modules frontend/
```

### 3. Integración de Tauri en el Frontend
Para que Tauri se comportara como el "compilador/envoltorio" exclusivo del frontend web, se movió su núcleo dentro de la carpeta frontend:
```bash
mv src-tauri frontend/src-tauri
```

### 4. Actualización de Configuraciones
Se modificaron las rutas relativas en dos archivos clave para que el sistema supiera dónde encontrar las cosas:

**En `frontend/src-tauri/tauri.conf.json`:**
Se simplificaron los comandos de compilación ya que ahora Tauri vive junto al `package.json`.
```json
"build": {
  "beforeDevCommand": "npm run dev",
  "beforeBuildCommand": "npm run build",
  "frontendDist": "../dist"
}
```

**En `docker-compose.yml`:**
Se actualizó la ruta de construcción del backend de `./backend-python` a `./backend`.

### 5. Limpieza de Caché (Solución de Errores)
Debido a que movimos la carpeta de Rust (`src-tauri`), el compilador (Cargo) fallaba buscando archivos en rutas absolutas antiguas que estaban guardadas en su memoria caché.
La solución fue limpiar ese historial:
```bash
cd frontend/src-tauri
cargo clean
```
*(Esto liberó más de 7 GB de caché obsoleta y permitió que Tauri compilara exitosamente con las nuevas rutas).*
