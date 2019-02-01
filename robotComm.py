from time import time
import random
from src.sender import PollySender

from src.color_extractor.color_extractor import ImageToColor
import numpy as np
import os 

ps = PollySender()
npz = np.load(os.path.join('src','color_extractor','color_names.npz'))
img_to_color = ImageToColor(npz['samples'], npz['labels'])

# ad = attributeDetector()

def crop_img(img,target):
    startx = int(target['topleft']['x'])
    starty = int(target['topleft']['y'])
    endx = int(target['bottomright']['x'])
    endy = int(target['bottomright']['y'])

    return img[starty:endy,startx:endx]

def resetVar(v):
    print("Reset Var")
    return {
                'target_id' : None,
                'target_color' : None,

                'prev_target_id' : None,

                'flag' : None,

                'spoken_flag' : {
                    'new': False,
                    'clothes_color': False,
                    'face': False
                },

                'robot_speed' : {
                    'prev': 0,
                    'target': 0
                },

                'head_hor_speed' : {
                    'prev': 0,
                    'target': 0
                },

                'head_ver_speed' : {
                    'prev': 0,
                    'target': 0
                },

                'robot_hor_movement_time' : None,
                'robot_ver_movement_time' : None
            }

def robotControl(_var, robot_ip, client_socket, robot_face, largest_face_name, largest_face_location, frame):
    _s = 0
    target = None
    if _var is None:
        _var = resetVar(_var)

    previous_hor_movement_time = _var['robot_hor_movement_time']
    previous_ver_movement_time = _var['robot_ver_movement_time']

    _var['target_id'] = largest_face_name

    _c = frame.shape[1] / 2
    center = ( largest_face_location[1]*4 + largest_face_location[3]*4 ) / 2
    width = largest_face_location[1]*4 - largest_face_location[3]*4
    height = largest_face_location[2]*4 - largest_face_location[0]*4

    _c_ver = frame.shape[0] / 2
    center_ver = ( largest_face_location[2]*4 + largest_face_location[0]*4 ) / 2
    # print(_c_ver, center_ver)
    '''
    1. 타겟 크기가 일정 크기보다 크면 좌우를 찾기 힘들기 때문에 일정 크기 이상일 시 정지하는게 좋아보임. (완)
    2. 타켓 센터와 뷰 센터의 거리가 멀면 더 빠르게 이동할 것 (완)
    3. 바운더리 바깥에서 접근할 시(센서값으로 바운더리인지 확인), 처음부터 빠르게 이동할 필요가 있음. (완)
    4. 타임 버퍼를 두어서 새로 발견된 타겟은 바로 추적하고, 따라잡았을 경우엔 움직이지 않게 해야함. (완)
    '''
    movement_buffer = 0.12

    hor_direction = '11'
    ver_direction = '11'
    speed = '1011'
    polly_msg = None

    # 190131 Todo
    # 상하/좌우 이동 시간 추적(hor_delta_t)을 분리 (완)
    if previous_hor_movement_time is not None:
        hor_delta_t = time() - previous_hor_movement_time
    else:
        hor_delta_t = None

    if previous_ver_movement_time is not None:
        ver_delta_t = time() - previous_ver_movement_time
    else:
        ver_delta_t = None

    '''
    이동 유무 및 방향 계산
    '''

    if hor_delta_t is not None:
        if hor_delta_t < 5:
            # 좌우 방향 추적 중 -> 이동 버퍼 작동
            if _c >= center * (1+movement_buffer):
                # 우로 이동
                hor_direction = '01'
                
            elif _c <= center * (1-movement_buffer):
                # 좌로 이동
                hor_direction = '10'

            else:
                # 정지
                hor_direction = '11'

                hor_movement_time = None

    if ver_delta_t is not None:
        if ver_delta_t < 5:
            # 상하 추적 중 -> 이동 버퍼 작동
            if _c_ver >= center_ver * (1+movement_buffer):
                # 우로 이동
                ver_direction = '01'
                
            elif _c_ver <= center_ver * (1-movement_buffer):
                # 좌로 이동
                ver_direction = '10'

            else:
                # 정지
                ver_direction = '11'

                ver_movement_time = None

    # print('detect_ratio', width / (center * 2))
    
    # print(hor_delta_t)
    if hor_delta_t is None or hor_delta_t >= 5:
        # 대기상태 -> 즉시 이동
        if _c >= center:
            # 우로 이동
            hor_direction = '01'
            
        elif _c <= center:
            # 좌로 이동
            hor_direction = '10'

    if ver_delta_t is None or ver_delta_t >= 5:
        # 대기상태 -> 즉시 이동
        if _c_ver >= center_ver:
            # 우로 이동
            ver_direction = '01'
            
        elif _c_ver <= center_ver:
            # 좌로 이동
            ver_direction = '10'
    
    # else:
    #     hor_direction = '11'

        

    '''
    타겟과의 거리에 따른 로봇 이동 속도 계산
    타겟과의 거리에 따른 고개 좌우 이동 속도 계산
    타겟과의 거리에 따른 고개 상하 이동 속도 계산
    '''
    _horizontal_distance = abs(_c - center)
    _vertical_distance = abs(_c_ver - center_ver)

    _horizontal_distance_ratio = _horizontal_distance / _c
    _vertical_distance_ratio = _vertical_distance / _c_ver

    # 가운데에서 떨어진 정도
    if _horizontal_distance_ratio < 0.3:
        hor_direction = '11'

        hor_movement_time = None

    if _vertical_distance_ratio < 0.4:
        ver_direction = '11'

        ver_movement_time = None

    _speed_interval = 0.4

    # print("Distance ratio",_horizontal_distance_ratio, _vertical_distance_ratio)

    # Todo 190131
    # 거리 비율에 따라서 목표 속도값을 지정
    if _horizontal_distance_ratio >= (1-_speed_interval):
        _robot_hor_s = 1
    elif _horizontal_distance_ratio >= (1-_speed_interval*2) and _horizontal_distance_ratio < (1-_speed_interval*1):
        _robot_hor_s = 2
    elif _horizontal_distance_ratio <= (1-_speed_interval*2):
        _robot_hor_s = 3

    if _vertical_distance_ratio >= (1-_speed_interval):
        _robot_ver_s = 1
    elif _vertical_distance_ratio >= (1-_speed_interval*2) and _vertical_distance_ratio < (1-_speed_interval*1):
        _robot_ver_s = 2
    elif _vertical_distance_ratio <= (1-_speed_interval*2):
        _robot_ver_s = 3

    # Todo 190131
    # prev_robot_speed와 target_robot_speed, robot_speed_acc 변수를 지정해서 스피드가 변화하게
    # acc값은 목표 속도와 현재 속도의 차이에 따라 차등 적용 혹은 일정 비율로.
    if _robot_hor_s == 1:
        robot_speed = '020'
        hor_speed = '010'

    elif _robot_hor_s == 2:
        robot_speed = '050'
        hor_speed = '020'

    elif _robot_hor_s == 3:
        robot_speed = '080'
        hor_speed = '030'

    if _robot_ver_s == 1:
        ver_speed = '010'

    elif _robot_ver_s == 2:
        ver_speed = '020'

    elif _robot_ver_s == 3:
        ver_speed = '030'

    # print(_horizontal_distance, hor_direction ,robot_speed)
    if hor_direction != '11':
        hor_movement_time = time()

    if ver_direction != '11':
        ver_movement_time = time()

    if hor_direction != '11' or ver_direction != '11':

        _m = "".join(['STX',hor_direction,robot_speed,hor_direction,hor_speed,ver_direction,ver_speed,robot_face,'ETX'])
        # _m = str(len(_m)).zfill(4) + _m
        # print(hor_direction, ver_direction)
        print(_m, hor_direction, ver_direction)
        if client_socket is not None:
            client_socket.send(_m.encode())

    # '''
    # 음성 재생
    # '''
    # print("Start:",_var)
    
    # # print("Target ID:", _var['target_id'], "Prev ID:", _var['prev_target_id'])
    # if _var['spoken_flag']['new'] == False:
    #     _var['flag'] = 'new'

    # if _var['prev_target_id'] is not None and _var['target_id'] != _var['prev_target_id']:
    #     # 신규 추적 대상
    #     _var = resetVar(_var)
    #     _var['flag'] = 'new'

    # try:
    #     if _var['spoken_flag']['new'] is True and _var['spoken_flag']['clothes_color'] is False:
    #         target_img_box = crop_img(frame, target)
    #         c = img_to_color.get(target_img_box)
    #         if _var['spoken_flag']['clothes_color'] == False and len(c) > 0 and _var['spoken_flag']['new'] == True:
    #             _var['target_color'] = c[0]
    #             # print(_var['target_color'])
    #             _var['flag'] = 'clothes_color'
    # except Exception as ex:
    #     pass

    # if _var['spoken_flag']['new'] is True and _var['spoken_flag']['face'] is False: 
    #     _r = ad.echo(_var['target_id'])
    #     # print(_r)

    # if ps._t is None or ps._t.isAlive() is False:
    #     if _var['flag'] == 'new':
    #         polly_msg = random.choice(['안녕하세요!', '반가워요!', '반갑습니다.', '어서오세요'])
    #         _var['prev_target_id'] = _var['target_id']
    #         _var['spoken_flag']['new'] = True
    #     elif _var['flag'] == 'clothes_color':
    #         _var['spoken_flag']['clothes_color'] = True

    #         if _var['target_color'] == 'blue':
    #             polly_msg = '파란옷이 잘 어울리시네요.'
                
    #         elif _var['target_color'] == 'red':
    #             polly_msg = '빨간옷이 잘 어울리시네요.'
                
    #         else:
    #             _var['spoken_flag']['clothes_color'] = False
            
    #     else:
    #         polly_msg = None

    #     if polly_msg is not None:
    #         ps.send(robot_ip, polly_msg)
    #         _var['flag'] = None
    #         polly_msg = None

    # data = ''
    # print("End:",_var)
    _var['robot_hor_movement_time'] = hor_movement_time
    _var['robot_ver_movement_time'] = ver_movement_time

    return _var