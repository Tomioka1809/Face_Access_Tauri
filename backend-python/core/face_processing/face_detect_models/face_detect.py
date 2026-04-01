import numpy as np
import mediapipe as mp
import cv2
import os
import time
from typing import Tuple, Any
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

class FaceDetectMediapipe:
    def __init__(self):
        # media pipe
        model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models', 'blaze_face_short_range.tflite'))
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.FaceDetectorOptions(
            base_options=base_options, 
            running_mode=vision.RunningMode.VIDEO,
            min_detection_confidence=0.7)
        self.face_detector_mp = vision.FaceDetector.create_from_options(options)
        self.bbox = []
        self.face_points = []
        self.last_timestamp_ms = -1

    def face_detect_mediapipe(self, face_image:np.ndarray)->Tuple[bool,Any]:
        rgb_image = face_image.copy()
        rgb_image = cv2.cvtColor(rgb_image,cv2.COLOR_BGR2RGB)
        
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)
        timestamp_ms = int(time.time() * 1000)
        if timestamp_ms <= self.last_timestamp_ms:
            timestamp_ms = self.last_timestamp_ms + 1
        self.last_timestamp_ms = timestamp_ms
        faces = self.face_detector_mp.detect_for_video(mp_image, timestamp_ms)
        
        if len(faces.detections) == 0:
            return False,faces
        else:
            return True,faces

    def extract_face_bbox_mediapipe(self,width_img:int,height_img:int,face_info:Any) :
        self.bbox = []
        for face in face_info.detections:
            bbox = face.bounding_box
            xi,yi,w_face,h_face = bbox.origin_x, bbox.origin_y, bbox.width, bbox.height
            xf,yf = xi+w_face, yi+h_face
            
            xi = max(0,xi)
            yi = max(0,yi)
            xf = min(width_img,xf)
            yf = min(height_img,yf)

            self.bbox = [xi,yi,xf,yf]

        return self.bbox

    def extract_face_points_mediapipe(self,width_img:int,height_img:int,face_info:Any) :
        self.face_points = []
        for face in face_info.detections:
            keypoints = face.keypoints
            if keypoints:
                for points in keypoints:
                    x,y = int(points.x * width_img),int(points.y * height_img)
                    self.face_points.append([x,y])
        return self.face_points
