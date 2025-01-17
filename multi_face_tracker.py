import face_recognition
import cv2

from src.sort.sort import *
from src.levi_hassner import LeviHassnerNet

import time
import math

# This is a demo of running face recognition on live video from your webcam. It's a little more complicated than the
# other example, but it includes some basic performance tweaks to make things run a lot faster:
#   1. Process each video frame at 1/4 resolution (though still display it at full resolution)
#   2. Only detect faces in every other frame of video.

# PLEASE NOTE: This example requires OpenCV (the `cv2` library) to be installed only to read from your webcam.
# OpenCV is *not* required to use the face_recognition library. It's only required if you want to run this
# specific demo. If you have trouble installing it, try any of the other demos that don't require it instead.

class MultiFaceTracker:
    def __init__(self,  video_device_ids=None, 
                        face_scan_depth=[3,1],
                        enable_age_gender=[False,True], 
                        age_gender_model_path=None, 
                        face_size=256,
                        age_type="min",
                        data_remove_time=3600):        
        # Get a reference to webcam #0 (the default one)
        if video_device_ids is not None and len(video_device_ids) == 2:
            self.video_capture_lg = cv2.VideoCapture(video_device_ids[0])
            self.video_capture = cv2.VideoCapture(video_device_ids[1])
            self.face_scan_depth = [3,1]
        else: 
            self.video_capture = None

        self.mot_tracker = Sort() 

        # Initialize some variables
        self.known_face_encodings = []
        self.known_face_names = []
        self.known_face_times = []
        self.known_face_ids = []
        self.known_face_ages = []
        self.known_face_genders = []
        self.known_face_detect_count = []

        self.face_locations = []
        self.face_encodings = []
        self.face_names = []
        self.process_this_frame = True

        self.data_remove_time = data_remove_time

        # Load Age/Gender Classification Module
        self.enable_age_gender = enable_age_gender
        for i in [0,1]:
            if enable_age_gender[i] is True:
                self.age_gender_model = LeviHassnerNet(image_size=face_size, model_path=age_gender_model_path)
                self.age_type = age_type

    def _track(self, face_locations):
        _fl = []
        for b in face_locations:
            _b = [b[3],b[0],b[1],b[2],1.0]
            _fl.append(_b)

        return list(self.mot_tracker.update(np.asarray(_fl)))

    def _remove_old_trackers(self):
        new_known_face_times = self.known_face_times
        current_time = time.time()
        for i, t in enumerate(self.known_face_times):
            if current_time - t > self.data_remove_time:
                del self.known_face_encodings[i]
                del self.known_face_names[i]
                del new_known_face_times[i]

        self.known_face_times = new_known_face_times

    def _crop_face(self, imgarray, section, margin=20, size=64):
        """
        :param imgarray: full image
        :param section: face detected area (x, y, w, h)
        :param margin: add some margin to the face detected area to include a full head
        :param size: the result image resolution with be (size x size)
        :return: resized image in numpy array with shape (size x size x 3)
        """
        img_h, img_w, _ = imgarray.shape
        if section is None:
            section = [0, 0, img_w, img_h]
        (x, y, w, h) = section
        margin = int(min(w,h) * margin / 100)
        x_a = x - margin
        y_a = y - margin
        x_b = x + w + margin
        y_b = y + h + margin
        if x_a < 0:
            x_b = min(x_b - x_a, img_w-1)
            x_a = 0
        if y_a < 0:
            y_b = min(y_b - y_a, img_h-1)
            y_a = 0
        if x_b > img_w:
            x_a = max(x_a - (x_b - img_w), 0)
            x_b = img_w
        if y_b > img_h:
            y_a = max(y_a - (y_b - img_h), 0)
            y_b = img_h
        cropped = imgarray[y_a: y_b, x_a: x_b]
        resized_img = cv2.resize(cropped, (size, size), interpolation=cv2.INTER_AREA)
        resized_img = np.array(resized_img)
        return resized_img #, (x_a, y_a, x_b - x_a, y_b - y_a)

    def _get_face_imgs(self, img, face_locations, face_size=256):
        face_imgs = np.empty((len(face_locations), face_size, face_size, 3))
        for i, b in enumerate(face_locations):
            _img = self._crop_face(img, (b[3],b[0],b[1]-b[3],b[2]-b[0]),margin=40, size=face_size) / 256.
            # _img /= 256.

            face_imgs[i,:,:,:] = _img
        return face_imgs

    def _get_box_area(self, box_location):
        _w = box_location[1] - box_location[3]
        _h = box_location[2] - box_location[0]
        _a = _w * _h

        return _a

    def _get_box_distance(self, b1, b2):
        p1 = [int((b1[1]+b1[3])/2), int((b1[0]+b1[2])/2)]
        p2 = [int((b2[1]+b2[3])/2), int((b2[0]+b2[2])/2)]

        distance = math.sqrt( ((p1[0]-p2[0])**2)+((p1[1]-p2[1])**2) )

        return distance

    def get_face_location(self):
        # returns actual face locations wrt frame size
        _l = self.face_locations * 4
        # print(_l)
        return _l

    def select_largest_face(self):
        a = 0
        index = None
        for _i, b in enumerate(self.face_locations):
            _a = self._get_box_area(box_location=b)
            
            if _a > a:
                a = _a
                index = _i

        return index

    def get_relevant_faces(self, index, area_margin=10, distance_margin=2.3):
        _target_face_index = []
        _target_face_location = self.face_locations[index]
        _target_face_area = self._get_box_area(_target_face_location)
        _target_face_width = _target_face_location[1] - _target_face_location[3]

        for i, b in enumerate(self.face_locations):
            _a = self._get_box_area(box_location=b)
            _d = self._get_box_distance(b1=_target_face_location, b2=b)
            # print(_d)
            if _target_face_area * (1+area_margin*0.01) > _a and _a > _target_face_area * (1-area_margin*0.01) and _d < _target_face_width * distance_margin:
                _target_face_index.append(i)

        return _target_face_index

    def run(self, frame, draw_on_img=True):
        try:
            # Resize frame of video to 1/4 size for faster face recognition processing
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

            # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
            rgb_small_frame = small_frame[:, :, ::-1]

            # Only process every other frame of video to save time
            if self.process_this_frame:
                # Find all the faces and face encodings in the current frame of video
                # N, E, S, W coordinates
                # number_of_times_to_upsample가 높을수록 멀리 있는 얼굴 detect. 속도 느려짐
                # 경험상 3일때 2m~3m
                
                self.face_locations = face_recognition.face_locations(rgb_small_frame, number_of_times_to_upsample=2)
                self.face_locations.sort(key=lambda x: x[3])
                
                # Get face images to get age and gender info
                if self.enable_age_gender:
                    face_imgs = self._get_face_imgs(rgb_small_frame, self.face_locations)
                    if len(face_imgs) > 0:
                        predicted_genders, predicted_ages = self.age_gender_model.predict(face_imgs)
                        # print(predicted_ages)

                self.face_encodings = face_recognition.face_encodings(rgb_small_frame, self.face_locations)
                
                self.face_names = []

                tracker = self._track(self.face_locations)
                tracker.sort(key=lambda x: x[0])

                for face_index, face_encoding in enumerate(self.face_encodings):
                    # See if the face is a match for the known face(s)
                    matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance=0.4)
                    name = "Unknown"

                    # If a match was found in known_face_encodings, just use the first one.
                    if True in matches:
                        first_match_index = matches.index(True)
                        
                        if self.enable_age_gender:
                            track_id = self.known_face_names[first_match_index].split("ID:")[1].split(",")[0]
                            gender = "M" if predicted_genders[face_index][0] > 0.5 else "F"
                            if self.age_type == "min":
                                prev_age = int(self.known_face_names[first_match_index].split("A:")[1])
                                age = int(predicted_ages[face_index] if prev_age > int(predicted_ages[face_index]) else prev_age)

                            elif self.age_type == "real":
                                age = int(predicted_ages[face_index])

                            elif self.age_type == "mean":
                                prev_age = int(self.known_face_names[first_match_index].split("A:")[1])
                                age = round((prev_age * self.known_face_detect_count[first_match_index] + int(predicted_ages[face_index])) / (self.known_face_detect_count[first_match_index]+1))

                            elif self.age_type == "mean_new":
                                prev_age = int(self.known_face_names[first_match_index].split("A:")[1])
                                age = round((prev_age * self.known_face_detect_count[first_match_index] + int(predicted_ages[face_index])) / (self.known_face_detect_count[first_match_index]+1))
                            
                            name = "ID:{}, G:{}, A:{}".format(track_id, gender, age)
                            
                            self.known_face_genders[first_match_index] = gender
                            self.known_face_ages[first_match_index] = age
                        else:
                            track_id = self.known_face_names[first_match_index].split("ID:")[1]
                            name = str(track_id)

                        self.known_face_names[first_match_index] = name
                        self.known_face_times[first_match_index] = time.time()

                        self.known_face_detect_count[first_match_index] += 1
                    else:
                        '''
                        # Select largest box as a target for tracing
                        known_face_encodings = [face_encodings[select_largest_face(face_locations)]]
                        known_face_names = ["Target"]
                        '''
                        if len(tracker) == len(self.face_locations):
                            self.known_face_encodings.append(face_encoding)
                            track_id = str(int(tracker[face_index][4]))

                            if self.enable_age_gender:
                                gender = "M" if predicted_genders[face_index][0] > 0.5 else "F"
                                age = int(predicted_ages[face_index])
                                name = "ID:{}, G:{}, A:{}".format(track_id, gender, age)
                                
                                self.known_face_genders.append(gender)
                                self.known_face_ages.append(age)
                                
                            else:
                                name = "ID:{}".format(track_id)

                            self.known_face_times.append(time.time())
                            self.known_face_names.append(name)
                            self.known_face_ids.append(track_id)
                            self.known_face_detect_count.append(1)
                            # name = track_id
                        
                        pass

                    self.face_names.append(name)
                    # print(known_face_names)

                # remove old data
                self._remove_old_trackers()

            self.process_this_frame = not self.process_this_frame

            if draw_on_img:
                # Display the results
                for (top, right, bottom, left), name in zip(self.face_locations, self.face_names):
                    # Scale back up face locations since the frame we detected in was scaled to 1/4 size
                    top *= 4
                    right *= 4
                    bottom *= 4
                    left *= 4

                    # Draw a box around the face
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

                    # Draw a label with a name below the face
                    cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
                    font = cv2.FONT_HERSHEY_DUPLEX
                    cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

            if self.video_capture is not None:
                # Display the resulting image
                cv2.imshow('Video', frame)
                # print("--")
                # Hit 'q' on the keyboard to quit!
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    return True

            return False# , self.face_locations*4
        except Exception as ex:
            print(ex)
            print("Camera off")

# moo_image = face_recognition.load_image_file("moo.png")
# moo_face_encoding = face_recognition.face_encodings(moo_image)[0]

# # Create arrays of known face encodings and their names
# known_face_encodings = [
#     moo_face_encoding
# ]
# known_face_names = [
#     "Hwanmoo Yong"
# ]

if __name__ == "__main__":
    # Initiate Face Tracker
    face_tracker = MultiFaceTracker(video_device_ids=[1,0], 
                                enable_age_gender=[False,True],
                                face_scan_depth=[3,1],
                                age_gender_model_path='./pretrained_models/age_gender/weights-wkfd.hdf5',
                                age_type="mean")

    # Initiate some variables
    _var = None

    robot_ip = None
    client_socket = None
    # robot_ip = "192.168.0.53"
    # client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # client_socket.connect((robot_ip, 8250))
    # print("Connected to the robot.")

    robot_face = '11'
    while True:
        # Grab a single frame of video
        ret, frame = face_tracker.video_capture.read()
        ret_lg, frame_lg = face_tracker.video_capture_lg.read()
        done = face_tracker.run(frame_lg)
        
        # Select largest face which is the closest one from the camera
        # Todo 190131
        # 기존의 Target ID가 특정(짧은) 안에 다시 잡힐경우 얼굴 크기가 달라져도 계속 추적
        # largest_face_index = face_tracker.select_largest_face()
        # if largest_face_index is not None:
        #     # Todo
        #     # 거리 Threshold 줘서 너무 멀면 버리게.
        #     # Select near faces from the closest face
        #     relevant_face_index = face_tracker.get_relevant_faces(largest_face_index)

        #     ages = [face_tracker.known_face_ages[i] for i in relevant_face_index]
        #     genders = [face_tracker.known_face_genders[i] for i in relevant_face_index]
        #     names = [face_tracker.known_face_names[i] for i in relevant_face_index]

        #     print(genders)
        #     # The actual robot part
        #     _var = robotControl(_var, robot_ip, client_socket, robot_face, face_tracker.known_face_names[largest_face_index], face_tracker.face_locations[largest_face_index], frame)

        # if done:
        #     # Release handle to the webcam
        #     face_tracker.video_capture.release()
