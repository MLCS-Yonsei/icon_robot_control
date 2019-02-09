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
    def __init__(self, robot_control, update_flag=False):
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
        self.wait_secs = 5 # 대기할 시간

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

        if not os.path.exists('audio'):
            os.makedirs('audio')
            self._download_audio_files()

        if update_flag == True:
            self._download_audio_files()

        self.robot_control = robot_control
        self.robot_ip = robot_control.robot_ip
        self.request_thread = None

        self.random_utterance = RandomUtterance(None, None)

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
            _audio = zipfile.read(name)
            _path = os.path.join('audio', name)
            with open(_path, 'wb') as f:
                f.write(_audio)
        print("All files are saved.")

    def _get_diff(self, l):
        return max(l) - min(l)
    
    def _get_avg(self, l):
        return sum(l) / float(len(l))

    def _get_path(self, file_name):
        return os.path.join('audio',file_name)

    def _send_play_request(self, path):
        def request_thread(robot_ip, path):
            if robot_ip is not None:
                url = "http://"+robot_ip+":3000/play"

                querystring = {"path":path,"speaker":"MJ"}

                response = requests.request("GET", url, params=querystring)
            else:
                print("TEST ENV. sleep for 1 secs", path)
                time.sleep(1)

        if self.request_thread is None or not self.request_thread.isAlive():
            self.request_thread = threading.Thread(target=request_thread, args=(self.robot_ip,path,))
            self.request_thread.start()
            # 발화 시작, 종료 후 4로 전환하고 n초만큼 대기. 
            self.status = 3

    def _check_status(self):
        result = False
        if self.request_thread is not None and not self.request_thread.isAlive():
            # 발화 종료됨. n초만큼 대기 후 status 2로 변경
            self.status = 2
            self.request_thread = None

            result = True

        if self.status < 2:
            result = True

        print("current status", self.status, "current stage", self.stage, "Thread", self.request_thread, "Result", result)
        return result

    def _select_audio(self, relation):
        print("Relation Check", self.current_relation, relation, self.current_relation == relation)
        if self.current_relation == relation:
            self.stage += 1
            
        else:
            self.stage = 1
            self.current_relation = relation
        
        if self.stage > 3:
            self.stage = 4

            print("All stage cleared. Random routine starts.")
            self._random_movement()

            self.stage = 0
            self.status = 1
        else:
            target_files = glob.glob(os.path.join('audio',relation+str(self.stage)+'*'))
            # target_file_path = self._get_path(random.choice(target_files))
            self._send_play_request(random.choice(target_files))

    def _random_movement(self):
        while True:
            done = self.random_utterance.run()
            print(done)
            if done == True:
                break
            else:
                _msg = self.random_utterance.msg()
                self.robot_control.send(_msg)

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
            self._select_audio('FRD')

    def utterance_for_kids(self, ages, genders):
        '''
        KID1xx.wav
        '''
        if self._check_status():
            print("utterance_for_kids", ages, genders, self.stage)
            self._select_audio('KID')

    def utterance_for_single(self, age, gender):
        '''
        SGL1xx.wav
        '''
        if self._check_status() and self.couple_not_cnt is None:
            print("utterance_for_single", age, gender, self.stage)
            self._select_audio('SGL')

    def _check_consistency(self, new_face_id):
        if self.target_face_id != new_face_id:
            self.stage = 0
            self.target_face_id = new_face_id

    def run(self, detect_cnts, ages, genders, emotions, emotion_probs, target_face_id):
        self._check_consistency(target_face_id)

        print(detect_cnts, ages, genders, emotions, emotion_probs)
        if min(detect_cnts) > 5:
            if len(ages) == 1:
                self.utterance_for_single(ages[0], genders[0])
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
