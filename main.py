from face_tracker import FaceTracker
from robot_control import RobotControl
from social_relation import SocialRelationEstimator
# import face_recognition
import socket
import sys 
import time
import os

# argv: 0 0 2 0


def main(video_src=2):
    # Initiate Face Tracker
    # Todo 190207
    # os.path에 해당 폴더 없으면 만들기
    face_tracker = FaceTracker(video_device_id=int(video_src), 
                                enable_age_gender=True,
                                age_gender_model_path=os.path.join('pretrained_models','age_gender','weights-wkfd.hdf5').replace("\\","/"),
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
        client_socket.bind(("0.0.0.0", 0))
        client_socket.connect((robot_ip, 8250))
        print("Connected to the robot.")


    audio_off = (sys.argv[4] == "0")


    robot_control = RobotControl(robot_ip, client_socket)
    robot_face = '05'
    target_face_index = None
    target_face_id_in_db = None
    
    if sys.argv[3] == "1":
        _update_flag = True
    else:
        _update_flag = False
        social_relation_estimator = SocialRelationEstimator(robot_control, update_flag=_update_flag, enable_speaker=True, audio_off=audio_off)

    while True:
        s_time = time.time()
        # Grab a single frame of video
        ret, frame = face_tracker.video_capture.read()
        process_frame = face_tracker.run(frame)
        move_flag = None

        if process_frame:
            # Select largest face which is the closest one from the camera
            # Todo 190131
            # Kalman filter Target ID가 특정(짧은) 안에 다시 잡힐경우 얼굴 크기가 달라져도 계속 추적 -> embedding group

            if target_face_id_in_db is None and len(face_tracker.known_faces.index_in_data) > 0 and len(face_tracker.known_faces.index_in_data) == len(face_tracker.face_locations):
                # 현재 face location들을 기반으로 가장 큰 얼굴의 index를 찾는다. 
                target_face_index = face_tracker.select_largest_face() # location 기반

                # 이 값은 DB에서의 ID값 -> 고유값
                target_face_id_in_db = face_tracker.known_faces.index_in_data[target_face_index] # Data 기반

                target_det_time = time.time()

            if target_face_id_in_db is not None:
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
                        if len(face_tracker.known_faces.index_in_data) > 0 and len(face_tracker.known_faces.index_in_data) == len(face_tracker.face_locations):
                            try:
                                # 현재 찾아낸 얼굴들의 순서를 기준으로 계속 타겟중인 얼굴의 ID가 몇번째에 위치하는지 찾기.
                                target_face_index = face_tracker.known_faces.index_in_data.index(target_face_id_in_db)
                                
                                # 현재 타겟의 이름
                                target_face_id = face_tracker.known_faces.names[target_face_id_in_db].trackid
                                # print('Target Face Name Id:',target_face_id)

                                # 현재 보이는 얼굴들의 순서에 DB의 ID값을 대입
                                # visible_face_index_in_db과 face_tracker.index_in_known_data는 같은듯..? Todo 190208 (완) - 같음
                                # visible_face_index_in_db = [face_tracker.index_in_known_data[i] for i, _ in enumerate(face_tracker.face_locations)]

                                # print(visible_face_index_in_db)
                                if target_face_id_in_db in face_tracker.known_faces.index_in_data:
                                    # 현재 보이는 얼굴들에 기존 타겟이 있음.
                                    '''
                                    move_flag
                                    0: 목표가 그대로 보임
                                    1: 목표가 보이지 않음 -> Slow Down
                                    2: 목표가 보이지 않고 새로운 대상 없음 -> Stop
                                    '''
                                    move_flag = 0
                                    target_face_location = face_tracker.face_locations[target_face_index]
                                    target_det_time = time.time()
                                else:
                                    # 목표가 현재 보이지 않음.
                                    move_flag = 1
                            except:
                                # print("target_face_id_in_db", target_face_id_in_db, face_tracker.index_in_known_data)
                                target_face_id = face_tracker.known_faces.names[target_face_id_in_db].track_id
                                # print('Target Face Name Id:',target_face_id)

                                for _vi, _visible_index in enumerate(face_tracker.known_faces.index_in_data):
                                    visible_face_id = face_tracker.known_faces.names[_visible_index].track_id
                                    
                                    if visible_face_id == target_face_id:
                                        # print('Visible Face Name Id:',visible_face_id)
                                        move_flag = 0
                                        target_face_location = face_tracker.face_locations[_vi]

                                # print(face_tracker.known_face_groups)

                                if move_flag != 0:
                                    # 목표가 사라졌고, 새로운 얼굴이 나타남
                                    if time.time() - target_det_time > 10:
                                        move_flag = 1
                                        target_face_index = None
                                        target_face_id_in_db = None
                                    else:
                                        move_flag = 1
                            
                        elif time.time() - target_det_time > 10:
                            move_flag = 2
                            target_face_index = None
                            target_face_id_in_db = None
                        else:
                            print("Detecting..")
                            move_flag = 1

                    elif time.time() - target_det_time > 5 and len(face_tracker.face_locations) == 0:
                        # 5초 이상 목표가 보이지 않을 시
                        move_flag = 2
                        target_face_index = None
                        target_face_id_in_db = None
                    else:
                        move_flag = 1
                # print("Move flag", move_flag)

                try:
                    target_name = face_tracker.known_faces.names[target_face_id_in_db]
                except:
                    target_name = None

                if move_flag == 0:
                    # The actual robot part
                    # print(target_face_location, type(target_face_location))
                    if face_tracker.center_location is not None:
                        target_face_location = face_tracker.center_location  # 두명 이상일 때 두명의 가운데를 보기. 문제 찾기

                    _var = robot_control.run(_var, 
                                        robot_face, 
                                        target_name, 
                                        target_face_location, 
                                        frame,
                                        move_flag, social_relation_estimator)
                else:
                    # The actual robot part
                    _var = robot_control.run(_var, 
                                        robot_face, 
                                        target_name, 
                                        None, 
                                        frame,
                                        move_flag, social_relation_estimator)

                # 관계 추정 부분 
                # print(robot_control.status)
                if robot_control.status == 0 and len(face_tracker.known_faces.ages) == len(face_tracker.known_faces.names):
                    # 거리가 일정 거리 이하고, Detect된 얼굴 면적 차이가 일정 크기 이하일 경우 Select
                    # social_relation_estimator.couple_not_cnt == None => 아무리 봐도 싱글

                    relevant_face_index = face_tracker.get_relevant_faces(target_face_index)
                    if len(relevant_face_index) >= 2:
                        face_tracker.center_location = face_tracker.get_center_location(relevant_face_index)
                        social_relation_estimator.couple_not_cnt = 0
                    elif social_relation_estimator.couple_not_cnt is not None:
                        social_relation_estimator.couple_not_cnt += 1

                        if social_relation_estimator.couple_not_cnt > 15:
                            face_tracker.center_location = None
                            social_relation_estimator.couple_not_cnt = None



                    ages = [face_tracker.known_faces.ages[face_tracker.known_faces.index_in_data[i]] for i in relevant_face_index]
                    genders = [face_tracker.known_faces.genders[face_tracker.known_faces.index_in_data[i]] for i in relevant_face_index]
                    names = [face_tracker.known_faces.names[face_tracker.known_faces.index_in_data[i]] for i in relevant_face_index]
                    emotions = [face_tracker.known_faces.emotions[face_tracker.known_faces.index_in_data[i]] for i in relevant_face_index]
                    emotion_probs = [face_tracker.known_faces.emotion_probs[face_tracker.known_faces.index_in_data[i]] for i in relevant_face_index]
                    detect_cnts = [face_tracker.known_faces.detect_count[face_tracker.known_faces.index_in_data[i]] for i in relevant_face_index]
                    # print(detect_cnts)

                    # Todo 190209 
                    # 특정 얼굴 크기 이상일때만 작동하게.

                    social_relation_estimator.run(detect_cnts, ages, genders, emotions, emotion_probs, target_face_id)
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
                                        2, social_relation_estimator)

            # delta = time.time() - s_time
            # print("Time Elapsed:", delta)
if __name__ == "__main__":
    main(video_src=sys.argv[1])
