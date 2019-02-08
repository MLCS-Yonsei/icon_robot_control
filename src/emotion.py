import logging
import sys
import numpy as np
from keras.models import Model, model_from_json
from keras.layers import Input, Activation, Dense, Flatten, Dropout
from keras.layers.convolutional import Conv2D, MaxPooling2D
from keras.layers.normalization import BatchNormalization
from keras.regularizers import l2
from keras.initializers import zeros, ones, random_normal
from keras import backend as K

import os
from io import BytesIO
from zipfile import ZipFile
from urllib.request import urlopen

import tensorflow as tf
from src.emotion_model import predict, image_to_tensor, deepnn

import cv2

class EmotionNet:
    def __init__(self, image_size=256, model_path="./pretrained_models/emotion"):
        if not os.path.isfile(os.path.join(model_path,'checkpoint')):
            if not os.path.exists(model_path):
                os.makedirs(model_path)

            print("Downloading checkpoint file...")
            resp = urlopen('http://hwanmoo.kr/files/emotion.zip')
            print("Download completed")
            zipfile = ZipFile(BytesIO(resp.read()))
            for name in zipfile.namelist():
                _ckpt = zipfile.read(name)
                _path = os.path.join(model_path, name)
                with open(_path, 'wb') as f:
                    f.write(_ckpt)
            print("All files are saved.")

        self.model = self.create_model( model_path = model_path)

        self.EMOTIONS = ['neutral','happiness','surprise','sadness','anger','disgust','fear','contempt','unknown','NF']
    
    def create_model(self, model_path):
        self.face_x = tf.placeholder(tf.float32, [None, 2304])
        y_conv = deepnn(self.face_x)
        self.probs = tf.nn.softmax(y_conv)

        saver = tf.train.Saver()
        ckpt = tf.train.get_checkpoint_state(model_path)
        sess = tf.Session()
        if ckpt and ckpt.model_checkpoint_path:
            saver.restore(sess, ckpt.model_checkpoint_path)
            # print('Restore model sucsses!!\nNOTE: Press SPACE on keyboard to capture face.')

        return sess

    def predict(self, face_imgs):
        def rgb2gray(rgb):
            return np.dot(rgb[...,:3], [0.299, 0.587, 0.114])

        _f_imgs = []
        for f in face_imgs:
            # res = cv2.resize(, dsize=(48, 48), interpolation=cv2.INTER_CUBIC)
            res = rgb2gray(f)
            _f_imgs.append(res)

        results = self.model.run(self.probs, feed_dict={self.face_x:image_to_tensor(_f_imgs)})

        emotion_results = []
        emotion_probs = []
        for r in results:
            emotion_results.append(self.EMOTIONS[r.tolist().index(max(r))])
            emotion_probs.append(max(r))

        # print(emotion_probs)
        return emotion_results, emotion_probs