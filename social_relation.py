import os
import glob
import time
import threading

from io import BytesIO
from zipfile import ZipFile
from urllib.request import urlopen
import requests
import random

from random_utterance import RandomUtterance

class SocialRelationEstimator:
    def __init__(self, robot_control, update_flag=False, enable_speaker=True, audio_off=False):
        # Todo190208
        # Stage 3에서 끝나고 나면 강제 랜덤 모션
        # 추적하다가 중도 포기할 알고리즘 2단계에서 다른 사람 등장..? Target_id로 구분?
        '''
        0 : 최초 상태
        1 : 스캔 중
        2 : 발화 대기
        3 : 발화중
        4 : 발화 중간 대기 - wait_time과 연동

        1일 경우 기존에 tracking 하던게 있는지 우선으로 보고 갈 것.
        -> ID를 체크해서 계속 같은 대상들을 추적하고 있을 경우, 가장 누적된 것으로 발화 
        '''
        self.status = 0
        self.couple_not_cnt = None
        self.wait_time = None
        self.wait_secs = None # 대기할 시간

        self.reset_emo_vars()

        self.min_detect_cnt = 8

        self.msg = ""

        self.audio_off = audio_off

        '''
        0 : 발화 전 
        1 : Initiate Joint Attention
        2 : Ensure Joint Attention
        3 : Convey Joint Attention
        4 : Random Movement

        Todo 190208
        4 완료 후 status 0으로, stage 0 or 1로 
        4는 랜덤 루틴에서 랜덤 무브만 강제로함. 
        '''
        self.stage = 0
        self.current_relation = None
        self.target_face_id = None
        self.last_target_face_id = None
        self.tracked_ids = []

        self.robot_control = robot_control
        self.robot_ip = robot_control.robot_ip

        if not os.path.exists('audio'):
            os.makedirs('audio')
            self._download_audio_files()

        if update_flag == True:
            self._download_audio_files()

        self.request_thread = None

        self.enable_speaker = enable_speaker

        self.random_utterance = RandomUtterance(None, None, None)

    def reset_emo_vars(self):
        self.emotion_flag = 0
        self.emo_time = None
        self.emo_wait_secs = 5.5
        self.emo_wait_cnt = 0
        self.emo_wait_limit = 2
        self.happiness_cnt = 0

    def _download_audio_files(self):
        if not os.path.exists('audio'):
            os.makedirs('audio')
        else:
            files = glob.glob(os.path.join('audio', '*'))
            for f in files:
                os.remove(f)

        print("Downloading audio files...")
        resp = urlopen('http://hwanmoo.kr/files/icon_audio.zip')
        print("Download completed")
        zipfile = ZipFile(BytesIO(resp.read()))
        for name in zipfile.namelist():
            print(name)
            _audio = zipfile.read(name)
            _path = os.path.join('audio', name)
            if name[0] != '_':
                with open(_path, 'wb') as f:
                    f.write(_audio)
        print("All files are saved.")

        # 로봇에 업데이트 신호 보내기
        # localhost:3000/update?path=audio&url=http://hwanmoo.kr/files/icon_audio.zip&flag=0
        if self.robot_ip is not None:
            resp = urlopen('http://'+self.robot_ip+':3000/update?path=audio&url=http://hwanmoo.kr/files/icon_audio.zip&flag=0')
            print("Updated on robot.")

    def _get_diff(self, l):
        return max(l) - min(l)
    
    def _get_avg(self, l):
        return sum(l) / float(len(l))

    def _get_path(self, file_name):
        return os.path.join('audio',file_name)

    def _send_play_request(self, path):
        def request_thread(robot_ip, path):
            if robot_ip is not None and self.enable_speaker is True:
                url = "http://"+robot_ip+":3000/play"

                querystring = {"path":path,"speaker":"MJ"}

                response = requests.request("GET", url, params=querystring)
            else:
                # print("TEST ENV. sleep for 1 secs", path)
                time.sleep(1)

        if self.request_thread is None or not self.request_thread.isAlive():
            self.request_thread = threading.Thread(target=request_thread, args=(self.robot_ip,path,))
            self.request_thread.start()
            # 발화 시작, 종료 후 4로 전환하고 n초만큼 대기. 
            self.status = 3

    def active_movement(self):
        def movement_thread(move):
            directions = ('01', '10')
            if move == 0:
                for i in range(6):
                    seq = i % 2
                    hor_direction = directions[seq]
                    robot_speed = '070'
                    hor_head_direction = directions[seq+1]
                    hor_speed = '070'
                    ver_direction = '11'
                    ver_speed = '050'
                    robot_face = random.choice(['01', '02'])
                    msg = "".join(
                        ['STX', hor_direction, robot_speed, hor_head_direction, hor_speed, ver_direction, ver_speed, robot_face,
                         'ETX'])

                    self.robot_control.send(msg)

            elif move == 1:
                pass

        move = random.randint(0, 0)
        threading.Thread(target=movement_thread, args=(move,) ).start()






    def emotion_routine_check(self):
        if self.stage == 2 and self.emotion_flag == 0:
            # print("Emo routine starts")
            # 감정 인식 시작 
            bypass_signal = False
            if len(self.emotions) == 1:
                if self.emotions[0] == "happiness" and self.emotion_probs[0] > 0.8:
                    bypass_signal = True
            else:
                if "happiness" in self.emotions and max(self.emotion_probs) > 0.8:
                    bypass_signal = True

            if bypass_signal == True:
                # print("Happiness Detected!")
                target_files = glob.glob(os.path.join('audio','EMO4'+'*'))
                if len(target_files) > 0:
                    # target_file_path = self._get_path(random.choice(target_files))
                    self._send_play_request(random.choice(target_files))

                self.reset_emo_vars()
                self.emotion_flag = 2
            else:
                self.emotion_flag = 1
                target_files = glob.glob(os.path.join('audio','EMO1'+'*'))
                if len(target_files) > 0:
                    # target_file_path = self._get_path(random.choice(target_files))
                    self._send_play_request(random.choice(target_files))

                self.emo_wait_cnt += 1
                self.emo_time = time.time()
        elif self.stage == 2 and self.emotion_flag == 1:
            # 감정 확인중 
            # print("Emo time", time.time() - self.emo_time, self.emotions)
            if len(self.emotions) == 1:
                if self.emotions[0] == "happiness" and self.emotion_probs[0] > 0.8:
                    self.happiness_cnt += 1
                    if self.happiness_cnt > 0:
                        print("Happiness Detected!")
                        target_files = glob.glob(os.path.join('audio','EMO2'+'*'))
                        if len(target_files) > 0:
                            # target_file_path = self._get_path(random.choice(target_files))
                            self._send_play_request(random.choice(target_files))

                        self.reset_emo_vars()
                        self.emotion_flag = 2
                        # sgl_utt(gender)
            else:
                if "happiness" in self.emotions and max(self.emotion_probs) > 0.8:
                    self.happiness_cnt += 1
                    if self.happiness_cnt > 0:
                        print("Happiness Detected!")
                        target_files = glob.glob(os.path.join('audio','EMO2'+'*'))
                        if len(target_files) > 0:
                            # target_file_path = self._get_path(random.choice(target_files))
                            self._send_play_request(random.choice(target_files))

                        self.reset_emo_vars()
                        self.emotion_flag = 2
                        # sgl_utt(gender)
            if self.emo_time is not None:
                if time.time() - self.emo_time > self.emo_wait_secs and self.emo_wait_cnt < 2:
                    print("Still not happy")
                    # Todo 190209
                    # 거절 시 멘트로. (완)
                    target_files = glob.glob(os.path.join('audio','EMO3'+'*'))
                    if len(target_files) > 0:
                        # target_file_path = self._get_path(random.choice(target_files))
                        self._send_play_request(random.choice(target_files))

                    self.emo_wait_cnt += 1
                    self.emo_time = time.time()
                elif time.time() - self.emo_time > self.emo_wait_secs and self.emo_wait_cnt == 2:
                    print("Giving up Emo routine")
                    target_files = glob.glob(os.path.join('audio','EMO6'+'*'))
                    if len(target_files) > 0:
                        # target_file_path = self._get_path(random.choice(target_files))
                        self._send_play_request(random.choice(target_files))

                    self.reset_emo_vars()
                    self.emotion_flag = 3
                    # sgl_utt(gender)

        else:
            return False

        return True

    def _check_status(self):
        result = False
        if self.request_thread is not None and not self.request_thread.isAlive():
            # 발화 종료됨. n초만큼 대기 후(status 4) status 2로 변경
            print("발화 종료")
            self.status = 4
            self.request_thread = None

            self.wait_time = time.time()
            self.wait_secs = random.uniform(0.8, 1.2)  # 대기할 시간
        else:
            if self.emotion_flag == 1 and self.status != 3:
                result = True
        
        if self.status == 4:
            if time.time() - self.wait_time > self.wait_secs:
                self.status = 2
                self.wait_time = None
                self.wait_secs = None

                result = True

        if self.status <= 2:
            result = True

        if result == True:
            emotion_signal = self.emotion_routine_check()
            if emotion_signal == False:
                result = True
            else:
                result = False

        # print(self.msg, "current status", self.status, "current stage", self.stage, "Thread", self.request_thread, "Result", result)
        return result

    def _select_audio(self, relation):
        if self.audio_off:
            return
        print("Relation Check", self.current_relation, relation, self.current_relation == relation, "stage", self.stage)
        if self.target_face_id in self.tracked_ids and self.stage == 0:

            # 마지막에 왔던 사람이 또 옴
            # 마지막 말고 역대로 추적했던 ID값을 다 가지고 있기 Todo
            if self.current_relation == relation:
                target_files = glob.glob(os.path.join('audio','REP'+'*'))
                self._send_play_request(random.choice(target_files))
                
                self.stage = 1
            
        else:

            if not self.target_face_id in self.tracked_ids:
                self.last_target_face_id = self.target_face_id
                self.tracked_ids.append(self.target_face_id)

            if self.current_relation == relation:
                self.stage += 1
                
            else:
                self.stage = 1
                self.current_relation = relation
            
            if self.stage > 4:
                self.stage = 5
                # self.stage = 0


                self.target_face_id = None
                # print("All stage cleared. Random routine starts.")
                self._random_movement()

                self.stage = 0
                self.status = 1
            else:
                if self.stage == 1:
                    # 인사말  
                    target_files = glob.glob(os.path.join('audio','GRT'+'*'))
                elif self.stage == 4:
                    target_files = glob.glob(os.path.join('audio','BYE'+'*'))
                else:
                    target_files = glob.glob(os.path.join('audio',relation+str(self.stage)+'*'))
                if len(target_files) > 0:
                    # target_file_path = self._get_path(random.choice(target_files))
                    self._send_play_request(random.choice(target_files))
                else:
                    print("No audio files.")

    def _random_movement(self):
        while True:
            done = self.random_utterance.run()
            time.sleep(0.5)
            # print(done)
            if done == True:
                break
            else:
                _msg = self.random_utterance.msg()
                # print(_msg)
                result = self.robot_control.send(_msg)
                if result == True:
                    print("Message sent") 

    def _check_consistency(self, new_face_id):
        if self.target_face_id != new_face_id:
            self.stage = 0
            self.target_face_id = new_face_id

    def utterance_for_family(self, ages, genders):
        '''
        FAM1xx.wav
        '''
        # if max(ages) > 35
        #     # 부모자식
        # else:
        #     # 형제/조카
        if self._check_status():
            print("utterance_for_family", ages, genders, self.stage)
            self._select_audio('FAM')

    def utterance_for_couple(self, ages, genders):
        '''
        CPL1xx.wav
        '''
        if self._check_status():
            print("utterance_for_couple", ages, genders, self.stage)
            self._select_audio('CPL')

    def utterance_for_friends(self, ages, genders):
        '''
        FRD1xx.wav
        '''
        if self._check_status():
            print("utterance_for_friends", ages, genders, self.stage)
            
            if genders[0] == "M":
                self._select_audio('FRM')
            else:
                self._select_audio('FRF')

    def utterance_for_kids(self, ages, genders):
        '''
        KID1xx.wav
        '''
        if self._check_status():
            print("utterance_for_kids", ages, genders, self.stage)
            self._select_audio('KID')

    def utterance_for_single(self, age, gender, emotion, emo_prob):
        '''
        SGL1xx.wav
        '''

        if self._check_status() and self.couple_not_cnt is None:
            print("utterance_for_single", age, gender, self.stage, self.emotion_flag)
            
            # if not self.emotion_routine_check():
            # 감정 루프에서 나감
            if gender == "M":
                self._select_audio('SGM')
            else:
                self._select_audio('SGF')
            self.emotion_flag = 0
    
    def run(self, detect_cnts, ages, genders, emotions, emotion_probs, target_face_id):
        self._check_consistency(target_face_id)

        self.emotions = emotions
        self.emotion_probs = emotion_probs

        # print(detect_cnts, ages, genders, emotions, emotion_probs)
        if min(detect_cnts) > self.min_detect_cnt:
            if len(ages) == 1:
                self.utterance_for_single(ages[0], genders[0], emotions[0], emotion_probs[0])
            elif len(ages) == 2:
                if genders[0] == genders[1]:
                    if self._get_diff(ages) <= 8:
                        if self._get_avg(ages) < 15:
                            # 아이들
                            self.utterance_for_kids(ages, genders)
                        else:
                            # 친구 혹은 형제자매
                            self.utterance_for_friends(ages, genders) 
                    else:
                        # 가족
                        self.utterance_for_family(ages, genders)

                else:
                    if self._get_diff(ages) <= 12:
                        if self._get_avg(ages) < 15:
                            # 아이들 
                            self.utterance_for_kids(ages, genders)
                        else:
                            # 커플
                            self.utterance_for_couple(ages, genders)
                    else:
                        # 가족 
                        self.utterance_for_family(ages, genders)
