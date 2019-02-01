from face_tracker import FaceTracker
from robotComm import robotControl
# import face_recognition
import socket

def main(video_src=2):
    # Initiate Face Tracker
    face_tracker = FaceTracker(video_device_id=2, 
                                enable_age_gender=True,
                                age_gender_model_path='./pretrained_models/age_gender/weights-wkfd.hdf5',
                                age_type="mean")

    # Initiate some variables
    _var = None

    robot_ip = "192.168.0.53"
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((robot_ip, 8250))
    print("Connected to the robot.")
    robot_face = '11'
    while True:
        # Grab a single frame of video
        ret, frame = face_tracker.video_capture.read()
        done = face_tracker.run(frame)
        
        # Select largest face which is the closest one from the camera
        # Todo 190131
        # 기존의 Target ID가 특정(짧은) 안에 다시 잡힐경우 얼굴 크기가 달라져도 계속 추적
        largest_face_index = face_tracker.select_largest_face()
        if largest_face_index is not None:
            # Todo
            # 거리 Threshold 줘서 너무 멀면 버리게.
            # Select near faces from the closest face
            relevant_face_index = face_tracker.get_relevant_faces(largest_face_index)

            ages = [face_tracker.known_face_ages[i] for i in relevant_face_index]
            genders = [face_tracker.known_face_genders[i] for i in relevant_face_index]
            names = [face_tracker.known_face_names[i] for i in relevant_face_index]

            print(genders)
            # The actual robot part
            _var = robotControl(_var, robot_ip, client_socket, robot_face, face_tracker.known_face_names[largest_face_index], face_tracker.face_locations[largest_face_index], frame)

        if done:
            # Release handle to the webcam
            face_tracker.video_capture.release()

if __name__ == "__main__":
    main(video_src=sys.argv[1])