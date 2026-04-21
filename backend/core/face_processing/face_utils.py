import os
import numpy as np
import cv2
import math
from typing import List, Tuple, Any

from core.face_processing.face_detect_models.face_detect import FaceDetectMediapipe
from core.face_processing.face_mesh_models.face_mesh import FaceMeshMediapipe  
from core.face_processing.face_matcher_models.face_matcher import FaceMatcherModels 

class FaceUtils:
    def __init__(self):
        #face detect
        self.face_detector = FaceDetectMediapipe()
        #face mesh
        self.mesh_detector = FaceMeshMediapipe()
        #face matcher
        self.face_matcher = FaceMatcherModels()
        
        #variables
        self.angle = None
        self.matching: bool = False
        self.distance: float = 0.0
    
    # --- DETECT ---
    def check_face(self, face_image: np.ndarray) -> Tuple[bool, Any, np.ndarray]:
        face_save = face_image.copy()
        check_face, face_info = self.face_detector.face_detect_mediapipe(face_image)
        return check_face, face_info, face_save

    def extract_face_bbox(self, face_image: np.ndarray, face_info: Any) -> List[int]:
        h_img, w_img, _ = face_image.shape
        return self.face_detector.extract_face_bbox_mediapipe(w_img, h_img, face_info)

    def extract_face_points(self, face_image: np.ndarray, face_info: Any):
        h_img, w_img, _ = face_image.shape
        return self.face_detector.extract_face_points_mediapipe(w_img, h_img, face_info)

    # --- CROP ---
    def face_crop(self, face_image: np.ndarray, face_bbox: List[int]) -> np.ndarray:
        h, w, _ = face_image.shape
        offset_x, offset_y = int(w * 0.025), int(h * 0.025)
        xi, yi, xf, yf = face_bbox
        xi = max(0, xi - offset_x)
        yi = max(0, yi - offset_y)
        xf = min(w, xf + offset_x)
        yf = min(h, yf)
        return face_image[yi:yf, xi:xf]
    
    # --- SAVE ---
    def save_face(self, face_crop: np.ndarray, user_code: str, path: str):
        if len(face_crop) != 0:
            if self.angle is not None and -5 < self.angle < 5:
                face_crop = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)
                cv2.imwrite(f"{path}/{user_code}.png", face_crop)
                return True
        return False

    # --- ALIGNED ---
    def face_rotate(self, face_image: np.ndarray, angle: float, center: Tuple):
        h, w, _ = face_image.shape
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        return cv2.warpAffine(face_image, M, (w, h))

    def calculate_rotation_angle(self, right_eye_x: int, right_eye_y: int, left_eye_x: int, left_eye_y: int):
        delta_x = left_eye_x - right_eye_x
        delta_y = left_eye_y - right_eye_y
        angle_rad = math.atan2(delta_y, delta_x)
        angle_deg = math.degrees(angle_rad)
        angle_deg %= 360
        return angle_deg

    def face_alignment(self, face_image: np.ndarray, face_key_points: List[List[int]]):
        h, w, _ = face_image.shape
        right_eye_x, right_eye_y = face_key_points[0][0], face_key_points[0][1]
        left_eye_x, left_eye_y = face_key_points[1][0], face_key_points[1][1]
        
        self.angle = self.calculate_rotation_angle(right_eye_x, right_eye_y, left_eye_x, left_eye_y)
        if self.angle > 180:
            self.angle -= 360
        center = ((right_eye_x + left_eye_x) // 2, (right_eye_y + left_eye_y) // 2)
        return self.face_rotate(face_image, self.angle, center)

    # --- MESH ---
    def face_mesh(self, face_image: np.ndarray) -> Tuple[bool, Any]:
        return self.mesh_detector.face_mesh_mediapipe(face_image)

    def extract_face_mesh(self, face_image: np.ndarray, face_mesh_info: Any) -> List[List[int]]:
        # viz=False para que no dibuje landmarks y nos ahorre todo el procesamiento GUI en el backend
        return self.mesh_detector.extract_face_mesh_points(face_image, face_mesh_info, viz=False)

    def check_face_center(self, face_points: List[List[int]]) -> bool:
        return self.mesh_detector.check_face_center(face_points)

    # --- MATCHER ---
    def face_matching(self, current_face: np.ndarray, face_db: List[np.ndarray], names_db: List[str]) -> Tuple[bool, str]:
        user_name: str = ''
        for idx, face_img in enumerate(face_db):
            current_face_rgb = cv2.cvtColor(current_face, cv2.COLOR_BGR2RGB)
            self.matching, self.distance = self.face_matcher.face_matching_arcface_model(current_face_rgb, face_img)
            
            if self.matching:
                user_name = names_db[idx]
                return self.matching, user_name
        
        return False, 'No face match!'