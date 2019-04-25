import os
import glob
import time
import threading

from io import BytesIO
from zipfile import ZipFile
from urllib.request import urlopen
import requests
import random



files = ["GRT01", "GRT02", "GRT03", "RND04", "RND05", "RND05", "RND06", "RND07", "RND08", "SGF2004", "SGF3001", "SGM2002", "SGM3001",
    "BYE01", "CPL2001", "CPL2002", "CPL2003", "CPL2004", "CPL3001", "CPL3002", "CPL3003"]
while True:
    path = input("enter file audio file: ")
    url = "http://" + "192.168.0.53" + ":3000/play"
    querystring = {"path": "audio\\" + path + ".wav", "speaker": "MJ"}
    response = requests.request("GET", url, params=querystring)

'''
audio\GRT01.wav
audio\GRT02.wav
audio\GRT03.wav

audio\REP01.wav

audio\RAND04.wav
audio\RAND05.wav
audio\RAND06.wav
audio\RAND07.wav
audio\RAND08.wav


audio\SGF2004.wav
audio\SGF3001.wav

audio\SGM2002.wav
audio\SGM3001.wav

audio\BYE01.wav

audio\CPL2001.wav
audio\CPL2002.wav
audio\CPL2003.wav
audio\CPL2004.wav

audio\CPL3001.wav
audio\CPL3002.wav
audio\CPL3003.wav

audio\EMO1001.wav
audio\EMO2001.wav
audio\EMO3001.wav
audio\EMO4001.wav
audio\EMO5001.wav
audio\EMO6001.wav


audio\FRF2001.wav
audio\FRF2003.wav
audio\FRF2004.wav
audio\FRF2005.wav

audio\FRF3001.wav
audio\FRF3002.wav

audio\FRM2001.wav
audio\FRM2002.wav
audio\FRM2003.wav
audio\FRM2004.wav

audio\FRM3001.wav
audio\FRM3002.wav




'''