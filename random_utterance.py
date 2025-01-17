import time
import random
import glob, os
import threading
import requests

class RandomUtterance:
    def __init__(self, robot_ip, robot_socket, robot_listen_queue):   
        '''
        Random Utterance 상황 flag
        0 : 초기 상태
        1 : Random Movement 시작함
        2 : Random utterance 시전함

        Flow : 0 -> 1 -> 2 (1 or 2회) -> (Face detect 여부 확인 후) 0 반복
        '''
        self.reset()
        self.enable_speaker = True
        self.robot_ip = robot_ip
        if robot_socket is None:
            self.robot_listen_q = None
        else:
            self.robot_listen_q = robot_listen_queue

    def reset(self):
        self.flag = 0
        self.robot_hor_direction = '11'
        self.robot_ver_direction = '11'

        # 편의상 고개와 본체 좌우 움직임은 동기화
        self.robot_hor_target_speed = random.randint(70, 100)
        self.robot_hor_prev_speed = 0

        self.robot_head_hor_target_speed = random.randint(15, 30)
        self.robot_head_hor_prev_speed = 0

        self.robot_ver_target_speed = random.randint(20, 40)
        self.robot_ver_prev_speed = 0

        self.robot_face = '01'

        self.init_time = time.time()
        self.listen_time = time.time()
        self.wait_time = None
        self.move_target_seconds = random.uniform(4.5, 7.5)

        self.request_thread = None

    def stop_robot(self):
        self.robot_hor_direction = '11'
        self.robot_ver_direction = '11'

        self.robot_hor_prev_speed = 0
        self.robot_head_hor_prev_speed = 0
        self.robot_ver_prev_speed = 0

    def msg(self):
        robot_speed = str(self.robot_hor_prev_speed).zfill(3)
        hor_speed = str(self.robot_head_hor_target_speed).zfill(3)
        ver_speed = str(self.robot_ver_prev_speed).zfill(3)

        return "".join(['STX',self.robot_hor_direction,robot_speed,self.robot_hor_direction,hor_speed,self.robot_ver_direction,ver_speed,self.robot_face,'ETX'])

    def get_direction(self):
        # 로봇 정보를 받아올 수 없거나 0.5초 이상 정보가 없을때 Direction은 랜덤.
        
        # if self.robot_listen_q is None or time.time() - self.listen_time > 0.5:
        #     if self.flag == 0:
        #         # 초기 상태에서만 결정
        #         self.robot_hor_direction = random.choice(['10','01'])
        #         self.robot_ver_direction = random.choice(['10','01'])
        # else:
        #     self.listen_time = time.time()
        #     # Todo 190207
        #     # q에서 정보 가져와서 Limit일 경우 디렉션 반대로 변경하기
        #     _l_msg = self.robot_listen_q.get()
        #     print("Random", _l_msg)
        if self.flag == 0:
            self.robot_hor_direction = random.choice(['10','01'])
            self.robot_ver_direction = random.choice(['10','01'])

    def run(self):
        if self.flag == 0:
            self.reset()
            self.get_direction()
            self.flag = 1 # 다음 루프에서 움직이기 시작함.

        elif self.flag == 1:
            # 목표 시간만큼 움직이기
            # print("time.time() - self.init_time", time.time() - self.init_time)
            if time.time() - self.init_time < self.move_target_seconds:
                # print("Robot moves")
                self.robot_hor_prev_speed = self.robot_hor_prev_speed + int((self.robot_hor_target_speed - self.robot_hor_prev_speed) / 10)
                self.robot_head_hor_prev_speed = self.robot_head_hor_prev_speed + int((self.robot_head_hor_target_speed - self.robot_head_hor_prev_speed) / 10)
                self.robot_ver_prev_speed = self.robot_ver_prev_speed + int((self.robot_ver_target_speed - self.robot_ver_prev_speed) / 10)

                self.get_direction()

            else:
                # 다 움직임
                self.stop_robot()
                self.wait_time = time.time() + 8 # 이 부분은 음성파일 길이만큼으로 조정 (플러스 버퍼시간)
                self.speak_cnt = random.randint(1,1)
                self.cur_speak_cnt = 0

                self.flag = 2

                # Movement가 끝남
                return True
        elif self.flag == 2:
            # print("Random Utterance, sleep for 8 seconds")

            if self.cur_speak_cnt < self.speak_cnt:
                # Todo 190207
                # Random utterance 음성 재생 + 랜덤으로 횟수 1-3
                # 1 ~ 3회 말함
                # if self.wait_time - time.time() > 0:
                #     # 아직 음성 재생중
                #     print("음성 재생중 : 남은 시간", self.wait_time - time.time())
                #     pass
                # else:
                #     # 음성 재생 완료 
                #     self.wait_time = time.time() + 8 # 이 부분은 음성파일 길이만큼으로 조정 (플러스 버퍼시간)
                #     self.cur_speak_cnt += 1
                #     print("음성 재생 완료: 재생 횟수", self.cur_speak_cnt)
                if self.request_thread is not None and not self.request_thread.isAlive():
                    # 발화 종료 
                    self.cur_speak_cnt += 1
                    self.request_thread = None
                elif self.request_thread is None:
                    self._send_play_request()

            else:
                # print("리셋")
                self.reset()

        return False

    def _send_play_request(self):
        target_files = glob.glob(os.path.join('audio','RND'+'*'))

        if len(target_files) == 0:
            print("No random utterance files.")
        else:
            path = random.choice(target_files)
            
            def request_thread(robot_ip, path):
                if robot_ip is not None and self.enable_speaker is True:
                    url = "http://"+robot_ip+":3000/play"

                    querystring = {"path":path,"speaker":"MJ"}

                    response = requests.request("GET", url, params=querystring)
                else:
                    print("TEST ENV. sleep for 1 secs", path)
                    time.sleep(1)

            if self.request_thread is None or not self.request_thread.isAlive():
                self.request_thread = threading.Thread(target=request_thread, args=(self.robot_ip,path,))
                self.request_thread.start()
