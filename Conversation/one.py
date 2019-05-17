import os
import glob
import time
import threading

from io import BytesIO
from zipfile import ZipFile
from urllib.request import urlopen
import requests
import random



# files = ["GRT01", "GRT02", "GRT03", "RND04", "RND05", "RND05", "RND06", "RND07", "RND08", "SGF2004", "SGF3001", "SGM2002", "SGM3001"
#     ,"BYE01", "CPL2001", "CPL2002", "CPL2003", "CPL2004", "CPL3001", "CPL3002", "CPL3003"]


files = ["RND06", "RND07", "RND08", "SGM2002", "SMG3001", "FRF3002", "GRT01", "GRT02", "sympathy1.wav"]

while True:

    print("1: 환영해\n2: 관심 좀 가져줘\n3: 그래...\n4: 여자친구는..?\n5: 레이싱게임 해볼래?\n6: 친구랑 커피쏘기\n7: 안녕\n8: 반가워\n 9: " )
    i = input("enter file audio file: ")
    index = int(i) - 1

    path = files[index]
    url = "http://" + "192.168.0.53" + ":3000/play"
    querystring = {"path": "audio\\" + path, "speaker": "MJ"}
    response = requests.request("GET", url, params=querystring)
