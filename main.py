from face_tracker import FaceTracker
from robot_control import RobotControl
from social_relation import SocialRelationEstimator
# import face_recognition
import socket
import sys 
import time
import os

def main(video_src=2):
    # Initiate Face Tracker
    # Todo 190207
    # os.path에 해당 폴더 없으면 만들기
    face_tracker = FaceTracker(video_device_id=int(video_src), 
                                enable_age_gender=True,
                                age_gender_model_path=os.path.join('pretrained_models','age_gender','weights-wkfd.hdf5').replace("\\","/"),
                                age_type="min")
    social_relation_estimator = SocialRelationEstimator()
    # Initiate some variables
    _var = None

    if sys.argv[2] == "0":
        robot_ip = None
        client_socket = None
    else:
        robot_ip = "192.168.0.53"
        print("Connecting to robot", robot_ip)
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.bind(("0.0.0.0", 0))
        client_socket.connect((robot_ip, 8250))
        print("Connected to the robot.")

    robot_control = RobotControl(robot_ip, client_socket)
    robot_face = '05'
    target_face_index = None
    target_face_index_in_db = None
    
    while True:
        s_time = time.time()
        # Grab a single frame of video
        ret, frame = face_tracker.video_capture.read()
        process_frame = face_tracker.run(frame)
        
        if process_frame:
            # Select largest face which is the closest one from the camera
            # Todo 190131
            # Kalman filter Target ID가 특정(짧은) 안에 다시 잡힐경우 얼굴 크기가 달라져도 계속 추적 -> embedding group
            if target_face_index_in_db is None and len(face_tracker.index_in_known_data) > 0 and len(face_tracker.index_in_known_data) == len(face_tracker.face_locations):
                target_face_index = face_tracker.select_largest_face() # location 기반
                target_face_index_in_db = face_tracker.index_in_known_data[target_face_index] # Data 기반

                target_det_time = time.time()

            if target_face_index_in_db is not None:
                '''
                1. 대상이 없을 경우 가장 큰 얼굴을 잡는다. # face_tracker.select_largest_face()
                2. 대상이 가장 큰 얼굴이 아니어도 기존에 추적중이었다면 쫓아간다.
                3. 대상이 사라졌을 경우 (5)초 동안은 대상을 유지하고 가던 방향으로 속도를 줄인다.
                '''
                random_utter_flag = robot_control.random_utterance.flag
                if random_utter_flag == 2:
                    # 랜덤 멘트 재생중
                    move_flag = 2
                else:
                    if len(face_tracker.face_locations) > 0:
                        # print(target_face_index, face_tracker.index_in_known_data)
                        if len(face_tracker.index_in_known_data) > 0 and len(face_tracker.index_in_known_data) == len(face_tracker.face_locations):
                            try:
                                target_face_index = face_tracker.index_in_known_data.index(target_face_index_in_db)

                                target_face_id = face_tracker.known_face_names[target_face_index_in_db].split("ID:")[1].split(",")[0]
                                print('Target Face Id:',target_face_id)
                                visible_face_index_in_db = [face_tracker.index_in_known_data[i] for i, _ in enumerate(face_tracker.face_locations)]
                                # print(visible_face_index_in_db)
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
                            except:
                                print("target_face_index_in_db",target_face_index_in_db,face_tracker.index_in_known_data)
                                # 목표가 사라졌고, 새로운 얼굴이 나타남
                                if time.time() - target_det_time > 5:
                                    move_flag = 2
                                    target_face_index = None
                                    target_face_index_in_db = None
                                else:
                                    move_flag = 1
                            
                        elif time.time() - target_det_time > 5:
                            move_flag = 2
                            target_face_index = None
                            target_face_index_in_db = None
                        else:
                            print("Detecting..")
                            move_flag = 1

                    elif time.time() - target_det_time > 5 and len(face_tracker.face_locations) == 0:
                        # 5초 이상 목표가 보이지 않을 시
                        move_flag = 2
                        target_face_index = None
                        target_face_index_in_db = None
                    else:
                        move_flag = 1
                print("Move flag", move_flag)

                try:
                    target_name = face_tracker.known_face_names[target_face_index_in_db]
                except:
                    target_name = None

                if move_flag == 0:
                    # The actual robot part
                    _var = robot_control.run(_var, 
                                        robot_face, 
                                        target_name, 
                                        face_tracker.face_locations[target_face_index], 
                                        frame,
                                        move_flag)
                else:
                    # The actual robot part
                    _var = robot_control.run(_var, 
                                        robot_face, 
                                        target_name, 
                                        None, 
                                        frame,
                                        move_flag)

                # 관계 추정 부분 
                # print(robot_control.status)
                if robot_control.status == 0 and len(face_tracker.known_face_ages) == len(face_tracker.known_face_names):
                    # 거리가 일정 거리 이하고, Detect된 얼굴 면적 차이가 일정 크기 이하일 경우 Select
                    print(target_face_index)
                    relevant_face_index = face_tracker.get_relevant_faces(target_face_index)

                    ages = [face_tracker.known_face_ages[face_tracker.index_in_known_data[i]] for i in relevant_face_index]
                    genders = [face_tracker.known_face_genders[face_tracker.index_in_known_data[i]] for i in relevant_face_index]
                    names = [face_tracker.known_face_names[face_tracker.index_in_known_data[i]] for i in relevant_face_index]
                    detect_cnts = [face_tracker.known_face_detect_count[face_tracker.index_in_known_data[i]] for i in relevant_face_index]
                    # print(detect_cnts)

                    social_relation_estimator.run(detect_cnts, ages, genders)
                    # print(min(detect_cnts))
                # if done:
                    # Release handle to the webcam
                    # face_tracker.video_capture.release()
                # except Exception as ex:
                #     print("ex at main loop:",ex)
            else:
                _var = robot_control.run(_var, 
                                        robot_face, 
                                        None, 
                                        None, 
                                        frame,
                                        2)

            # delta = time.time() - s_time
            # print("Time Elapsed:", delta)
if __name__ == "__main__":
    main(video_src=sys.argv[1])