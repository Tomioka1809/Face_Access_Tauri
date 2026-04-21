import os
import cv2
import numpy as np
import base64
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from core.database.config import SessionLocal
from core.database.models import User, AccessLog
from core.face_processing.face_utils import FaceUtils

router = APIRouter()
face_utils = FaceUtils()

FACES_DIR = os.path.join(os.path.dirname(__file__), "..", "database", "faces")
os.makedirs(FACES_DIR, exist_ok=True)

# Estado en memoria para acelerar la pipeline de login globalmente
db_cache_faces = []
db_cache_names = []
db_cache_ids = []

def load_database(db: Session):
    global db_cache_faces, db_cache_names, db_cache_ids
    db_cache_faces.clear()
    db_cache_names.clear()
    db_cache_ids.clear()
    
    users = db.query(User).filter(User.is_active == True).all()
    for user in users:
        if user.face_image_path and os.path.exists(user.face_image_path):
            img_read = cv2.imread(user.face_image_path)
            if img_read is not None:
                db_cache_faces.append(img_read)
                db_cache_names.append(user.user_code)
                db_cache_ids.append(user.id)

@router.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
    await websocket.accept()
    db = SessionLocal()
    
    # Refrescar caché de la Base de Datos
    load_database(db)
    
    frame_counter = 0
    
    try:
        while True:
            data = await websocket.receive_json()
            image_b64 = data.get("image")
            mode = data.get("mode", "idle")
            
            if not image_b64 or mode == "idle":
                await websocket.send_json({"status": "Esperando Acción...", "bbox": None})
                continue
                
            img_data = base64.b64decode(image_b64.split(",")[1])
            np_arr = np.frombuffer(img_data, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            state_msg = "Procesando"
            bbox_res = None
            access_granted = False
            mesh_points = None
            result_status = "pending"

            # Paso 1: Mesh para verificar que esté centrado (Barato y Rápido)
            check_face_mesh, face_mesh_info = face_utils.face_mesh(frame)
            
            if not check_face_mesh:
                await websocket.send_json({"status": "Rostro NO Detectado", "bbox": None})
                continue
                
            face_mesh_points = face_utils.extract_face_mesh(frame, face_mesh_info)
            mesh_points = face_mesh_points # Guardamos para enviarlo a React
            check_face_center = face_utils.check_face_center(face_mesh_points)
            
            if not check_face_center:
                await websocket.send_json({"status": "¡Centra tu rostro!", "bbox": None, "mesh": mesh_points})
                continue
                
            # Si pasamos a estar centrados:
            state_msg = "Analizando Rostro... Espera"
            frame_counter += 1
            
            # Recién en el fotograma 20 hacemos la evaluación ArcadeFace de peso completo
            check_face_detect, face_info, face_save = face_utils.check_face(frame)
            if check_face_detect:
                bbox_res = face_utils.extract_face_bbox(frame, face_info)
                face_points = face_utils.extract_face_points(frame, face_info)
                
                if frame_counter >= 20 and len(face_points) >= 2:
                    face_aligned = face_utils.face_alignment(face_save, face_points)
                    face_crop = face_utils.face_crop(face_aligned, bbox_res)
                    
                    if mode == "login":
                        matcher, user_name = face_utils.face_matching(face_crop, db_cache_faces, db_cache_names)
                        
                        if matcher:
                            state_msg = f"¡Bienvenido, {user_name}!"
                            access_granted = True
                            result_status = "success"
                            
                            # Log to Database
                            try:
                                ui = db_cache_ids[db_cache_names.index(user_name)]
                                db.add(AccessLog(user_id=ui, access_status="Approved"))
                                db.commit()
                            except:
                                pass
                        else:
                            state_msg = "Rostro no registrado, por favor regístrese"
                            result_status = "failed"
                            
                    elif mode == "signup":
                        username = data.get("username", "DemoUser")
                        password = data.get("password", "")
                        save_success = face_utils.save_face(face_crop, username, FACES_DIR)
                        
                        if save_success:
                            # 1. Verificar si el usuario ya existe
                            existing_user = db.query(User).filter(User.user_code == username).first()
                            face_path = os.path.join(FACES_DIR, f"{username}.png")
                            
                            if not existing_user:
                                new_user = User(user_code=username, password=password, face_image_path=face_path)
                                db.add(new_user)
                                db.commit()
                            else:
                                existing_user.face_image_path = face_path
                                existing_user.password = password
                                db.commit()
                                
                            state_msg = "¡Registro Exitoso!"
                            access_granted = True
                            result_status = "success"
                            
                            # Actualizamos la caché de la DB en memoria para poder autenticar de inmediato
                            load_database(db)
                        else:
                            state_msg = "Error al guardar rostro."
                            result_status = "failed"
                            
                    frame_counter = 0 # Reset para que vuelva a iniciar si el usuario intenta de nuevo

            await websocket.send_json({
                "status": state_msg,
                "bbox": bbox_res,
                "access": access_granted,
                "mesh": mesh_points,
                "result": result_status
            })
            
    except WebSocketDisconnect:
        print("React Frontend disconnected from WebSocket")
    finally:
        db.close()
