from face_tracker import FaceTracker
from robotComm import RobotControl
# import face_recognition
import socket
import sys 
import time

def main(video_src=2):
    # Initiate Face Tracker
    face_tracker = FaceTracker(video_device_id=int(video_src), 
                                enable_age_gender=True,
                                age_gender_model_path='./pretrained_models/age_gender/weights-wkfd.hdf5',
                                age_type="min")

    # Initiate some variables
    _var = None

    if sys.argv[2] == "0":
        robot_ip = None
        client_socket = None
    else:
        robot_ip = "192.168.0.53"
        print("Connecting to robot", robot_ip)
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((robot_ip, 8250))
        print("Connected to the robot.")

    robot_control = RobotControl(robot_ip, client_socket)
    robot_face = '11'
    target_face_index = None
    
    while True:
        # Grab a single frame of video
        ret, frame = face_tracker.video_capture.read()
        done = face_tracker.run(frame)
        
        # Select largest face which is the closest one from the camera
        # Todo 190131
        # Kalman filter Target ID가 특정(짧은) 안에 다시 잡힐경우 얼굴 크기가 달라져도 계속 추적 -> embedding group
        if target_face_index is None:
            target_face_index = face_tracker.select_largest_face() # location 기반
            target_det_time = time.time()

        if target_face_index is not None:
            '''
            1. 대상이 없을 경우 가장 큰 얼굴을 잡는다. # face_tracker.select_largest_face()
            2. 대상이 가장 큰 얼굴이 아니어도 기존에 추적중이었다면 쫓아간다.
            3. 대상이 사라졌을 경우 (5)초 동안은 대상을 유지하고 가던 방향으로 속도를 줄인다.
            '''
            if len(face_tracker.face_locations) > 0:
                print(target_face_index, face_tracker.index_in_known_data)
                if len(face_tracker.index_in_known_data) > 0:
                    target_face_index_in_db = face_tracker.index_in_known_data[target_face_index] # Data 기반
                    target_face_id = face_tracker.known_face_names[target_face_index_in_db].split("ID:")[1].split(",")[0]

                    visible_face_index_in_db = [face_tracker.index_in_known_data[i] for i, _ in enumerate(face_tracker.face_locations)]

                    if target_face_index_in_db in visible_face_index_in_db:
                        # 현재 보이는 얼굴들에 기존 목표가 있음.
                        '''
                        move_flag
                        0: 목표가 그대로 보임
                        1: 목표가 보이지 않음 -> Slow Down
                        2: 목표가 보이지 않고 새로운 대상 없음 -> Stop
                        '''
                        move_flag = 0
                        target_det_time = time.time()
                    else:
                        # 목표가 현재 보이지 않음.
                        move_flag = 1
                elif time.time() - target_det_time > 5:
                    move_flag = 2
                else:
                    move_flag = 1

            elif time.time() - target_det_time > 5 and len(face_tracker.face_locations) == 0:
                # 5초 이상 목표가 보이지 않을 시
                move_flag = 2
                target_face_index = None
            else:
                move_flag = 1
            print("Move flag", move_flag)
            # Todo
            # 거리 Threshold 줘서 너무 멀면 버리게.
            # Select near faces from the closest face

            if move_flag == 0 and len(face_tracker.known_face_ages) == len(face_tracker.known_face_names):
                relevant_face_index = face_tracker.get_relevant_faces(target_face_index)

                ages = [face_tracker.known_face_ages[face_tracker.index_in_known_data[i]] for i in relevant_face_index]
                genders = [face_tracker.known_face_genders[face_tracker.index_in_known_data[i]] for i in relevant_face_index]
                names = [face_tracker.known_face_names[face_tracker.index_in_known_data[i]] for i in relevant_face_index]
            if move_flag == 0:
                # The actual robot part
                _var = robot_control.run(_var, 
                                    robot_face, 
                                    face_tracker.known_face_names[target_face_index_in_db], 
                                    face_tracker.face_locations[target_face_index], 
                                    frame,
                                    move_flag)
            else:
                # The actual robot part
                _var = robot_control.run(_var, 
                                    robot_face, 
                                    face_tracker.known_face_names[target_face_index_in_db], 
                                    None, 
                                    frame,
                                    move_flag)

            if done:
                # Release handle to the webcam
                face_tracker.video_capture.release()
            # except Exception as ex:
            #     print("ex at main loop:",ex)

if __name__ == "__main__":
    main(video_src=sys.argv[1])