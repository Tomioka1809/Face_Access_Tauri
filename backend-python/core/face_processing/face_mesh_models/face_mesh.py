import numpy as np
import mediapipe as mp
import cv2
import os
import time
from typing import Any,List,Tuple
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

class FaceMeshMediapipe:
    def __init__(self):
        # mediapipe drawing config
        self.config_draw = {'color': (255, 127, 0), 'thickness': -1, 'circle_radius': 1}

        # tasks API
        model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models', 'face_landmarker.task'))
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_faces=1,
            min_face_detection_confidence=0.6,
            min_face_presence_confidence=0.6,
            min_tracking_confidence=0.6)
        self.face_mesh_mp = vision.FaceLandmarker.create_from_options(options)

        self.mesh_points = None
        self.last_timestamp_ms = -1
        # face points
        # right parietal
        self.rp_x: int = 0
        self.rp_y: int = 0
        # left parietal
        self.lp_x: int = 0
        self.lp_y: int = 0
        # right eyebrow
        self.re_x: int = 0
        self.re_y: int = 0
        # left eyebrow
        self.le_x: int = 0
        self.le_y: int = 0

    def face_mesh_mediapipe(self,face_image:np.ndarray) -> Tuple[bool,Any]:
        rgb_image = face_image.copy()
        rgb_image = cv2.cvtColor(rgb_image,cv2.COLOR_BGR2RGB)
        
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)
        timestamp_ms = int(time.time() * 1000)
        if timestamp_ms <= self.last_timestamp_ms:
            timestamp_ms = self.last_timestamp_ms + 1
        self.last_timestamp_ms = timestamp_ms
        face_mesh = self.face_mesh_mp.detect_for_video(mp_image, timestamp_ms)
        
        if len(face_mesh.face_landmarks) == 0:
            return False,face_mesh
        else:
            return True,face_mesh

    def extract_face_mesh_points(self,face_image:np.ndarray,face_mesh_info:Any,viz:bool) -> List[List[int]]:
        height,width,_ = face_image.shape
        self.mesh_points = []
        for face_landmarks in face_mesh_info.face_landmarks:
            for i,points in enumerate(face_landmarks):
                x,y = int(points.x * width),int(points.y * height)
                self.mesh_points.append([i,x,y])

                if viz:
                    cv2.circle(face_image, (x, y), self.config_draw['circle_radius'], self.config_draw['color'], self.config_draw['thickness'])
        return self.mesh_points

    def check_face_center(self,face_points:List[List[int]]) -> bool:
        if len(face_points) >= 468:
            self.rp_x,self.rp_y = face_points[139][1:]
            self.lp_x,self.lp_y = face_points[368][1:]
            self.re_x,self.re_y = face_points[70][1:]
            self.le_x,self.le_y = face_points[300][1:]

            # The original code used undefined 'face_image' in cv2.circle inside this method
            # Assuming face_image was globally accessible or meant to be ignored.
            # cv2.circle(face_image,(self.rp_x,self.rp_y),2,(0,255,0),2)
            
            if self.re_x > self.rp_x and self.le_x < self.lp_x:
                return True
            else:
                return False
        return False

    def config_color(self,color:Tuple[int,int,int]):
        self.config_draw['color'] = color
