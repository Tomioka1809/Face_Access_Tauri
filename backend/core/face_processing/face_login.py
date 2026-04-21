import numpy as np
from typing import Tuple

from core.face_processing.face_utils import FaceUtils
# from process.database.config import DatabasePath

class FaceLogIn:
    def __init__(self):
        self.face_utilities = FaceUtils()
        self.database = DatabasePath()

        self.matcher = None
        self.comparison = False
        self.count_frame = 0

    def process(self,face_image:np.ndarray):
        #step 1: check face mesh
        check_face_mesh,face_mesh_info = self.face_utilities.face_mesh(face_image)
        if check_face_mesh is False:
            return face_image,self.matcher,"No face mesh detected"
        
        #step 3: extract landmarks
        face_mesh_points_list = self.face_utilities.extract_face_mesh(face_image,face_mesh_info)
        
        #step 4: check face center
        check_face_center = self.face_utilities.check_face_center(face_mesh_points_list)

        #step 5: show state
        self.face_utilities.show_state_login(face_image,state=self.matcher)

        if check_face_center:
            #step 6: extract face info

            self.count_frame += 1
            if self.count_frame == 48:
                #run face detection for clipping
                check_face_detect,face_info,face_save = self.face_utilities.check_face(face_image)
                if check_face_detect is False:
                    return face_image,self.matcher,"No face detected for cropping"
                    
                #bbox & key_points
                face_bbox = self.face_utilities.extract_face_bbox(face_image,face_info) 
                face_points = self.face_utilities.extract_face_points(face_image,face_info)

                if len(face_points) < 2:
                    return face_image,self.matcher,'Not enough keypoints!'

                #step 7: face aligned
                face_aligned = self.face_utilities.face_alignment(face_save,face_points)

                #step 8: face crop
                face_crop = self.face_utilities.face_crop(face_aligned,face_bbox)

                #step 9: read database
                faces_database, names_database, info = self.face_utilities.read_face_database(self.database.faces)

                if len(faces_database) != 0 and not self.comparison and self.matcher is None:

                    #step 10: face matcher
                    self.matcher,user_name = self.face_utilities.face_matching(face_crop,faces_database,names_database)

                    if self.matcher:
                        #step 11: user register
                        self.face_utilities.user_check_in(user_name,self.database.users)
                        return face_image,self.matcher,'Approved user access!'

                    else:
                        return face_image,self.matcher,'Denied user access!'

                else:
                    return face_image,self.matcher,'Empty database!'
            else:
                return face_image,self.matcher,'waiting frames!'
        
        else:
            return face_image,self.matcher,'Face not centered!'
                
            

            

            
            

        