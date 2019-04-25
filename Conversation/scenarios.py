import os
import glob
import time
import threading

from io import BytesIO
from zipfile import ZipFile
from urllib.request import urlopen
import requests
import random


# FRM2002 남자 둘 쉽지 않은 만남
scenarios = [
    [("audio\GRT01.wav", 0), ("audio\RND06.wav", 1.5), ("audio\EMO1001.wav", 2), ("audio\RND04.wav", 1), ("audio\BYE01.wav", 0) ],  # 친구 둘, 웃어봐
    [("audio\GRT01.wav", 0), ("audio\RND06.wav", 0.5), ("audio\SGM2002.wav", 1), ("audio\FRF3001.wav", 0)],  # 남자 혼자
    [("audio\GRT03.wav", 0), ("audio\FRF2005.wav", 1), ("audio\EMO4001.wav", 1), ("audio\FRF3002", 2)],  # 여자 둘 남자친구는?
    [("audio\GRT03.wav", 0), ("audio\FRM2002.wav", 1), ("audio\EMO4001.wav", 1), ("audio\FRF3002", 2)],  # 남자둘 쉽지 않은 만
    [("audio\GRT02.wav", 1), ("audio\EMO4001.wav", 1), ("audio\CPL2002.wav", 2), ("audio\CPL3002.wav", 2.5), ("audio\BYE01.wav", 0)],  # 커플 남자듬직
    [("audio\GRT03.wav", 1.5), ("audio\CPL2004.wav", 2), ("audio\EMO4001.wav", 1), ("audio\CPL3002.wav", 3), ("audio\BYE01.wav", 0)],  # 커플 여자예쁨
    [("audio\GRT01.wav", 1), ("audio\EMO1001.wav", 1), ("audio\EMO2001.wav", 0.5), ("audio\FRF3001.wav", 2)],  # 표정이 왜그래 웃어봐
    [("audio\GRT02.wav", 1), ("audio\FRF2001.wav", 1), ("audio\EMO4001.wav", 0.6), ("audio\FRF3002.wav", 2)],  # 친구 둘 비슷 커피쏘기
    [("audio\GRT03.wav", 0), ("audio\FRF2003.wav", 1), ("audio\EMO4001.wav", 1), ("audio\FRF3002", 2)],  # 오른쪽 나이많음
]

while True:
    num = input("1: 친구 둘, 웃어봐\n2: 남자 혼자\n3: 여자 둘 남자친구는?\n4: 남자 둘 쉽지않은 만남\n5: 커플 남자듬직\n6: 커플 여자예쁨\
                \n7: 표정이 왜그래 웃어봐\n8: 친구 둘 비슷 커피쏘기\n9: 친구 둘 오른쪽 나이 많음\n")
    index = int(num) - 1
    files = scenarios[index]
    for i in range(len(files)):
        path = files[i][0]
        sleeptime = files[i][1]
        url = "http://" + "192.168.0.53" + ":3000/play"
        querystring = {"path": path, "speaker": "MJ"}
        response = requests.request("GET", url, params=querystring)
        time.sleep(sleeptime)
