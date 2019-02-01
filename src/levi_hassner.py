import logging
import sys
import numpy as np
from keras.models import Model
from keras.layers import Input, Activation, Dense, Flatten, Dropout
from keras.layers.convolutional import Conv2D, MaxPooling2D
from keras.layers.normalization import BatchNormalization
from keras.regularizers import l2
from keras.initializers import zeros, ones, random_normal
from keras import backend as K

import os.path
import urllib.request

sys.setrecursionlimit(2 ** 20)
np.random.seed(2 ** 10)


class LeviHassnerNet:
    def __init__(self, image_size=256, dropout_rate=0.5, model_path=None):
        self._weight_decay = 0.0005

        if K.image_dim_ordering() == "th":
            logging.debug("image_dim_ordering = 'th'")
            self._channel_axis = 1
            self._input_shape = (3, image_size, image_size)
        else:
            logging.debug("image_dim_ordering = 'tf'")
            self._channel_axis = -1
            self._input_shape = (image_size, image_size, 3)

        self.model = self.create_model(pkeep=dropout_rate, enable_bn=True)
        
        if model_path is not None:
            if os.path.isfile(model_path):
                self.model.load_weights(model_path)
            else:
                print("Downloading Weights...")
                urllib.request.urlretrieve("http://hwanmoo.kr/files/weights-wkfd.hdf5", model_path)
                print("Download completed")
                self.model.load_weights(model_path)

        # Load constants
        self._ages = np.arange(0, 101).reshape(101, 1)

    def create_model(self, pkeep=0.5, enable_bn=True):
        inputs = Input(shape=self._input_shape)
        # Convolution2D(n_filter, w_filter, h_filter, border_mode='same')(inputs)
        # Activation(activation='relu')()
        # return BatchNormalization()()
        conv1 = Conv2D( filters=96, kernel_size=(7, 7),
                        strides=(4, 4),
                        padding="valid",
                        kernel_initializer=random_normal(stddev=0.01),
                        kernel_regularizer=l2(self._weight_decay),
                        bias_initializer=zeros())(inputs)
        if enable_bn: conv1 = BatchNormalization(axis=self._channel_axis, momentum=0.9997)(conv1)
        pool1 = MaxPooling2D(pool_size=3, strides=2)(conv1)

        conv2 = Conv2D( filters=256, 
                        kernel_size=(5, 5),
                        strides=(1, 1),
                        padding="same",
                        kernel_initializer=random_normal(stddev=0.01),
                        kernel_regularizer=l2(self._weight_decay),
                        bias_initializer=ones())(pool1)  # "One conv at the beginning (spatial size: 32x32)"
        if enable_bn: conv2 = BatchNormalization(axis=self._channel_axis, momentum=0.9997)(conv2)
        pool2 = MaxPooling2D(pool_size=3, strides=2)(conv2)

        conv3 = Conv2D( filters=384, 
                        kernel_size=(3, 3),
                        strides=(1, 1),
                        padding="same",
                        kernel_initializer=random_normal(stddev=0.01),
                        kernel_regularizer=l2(self._weight_decay),
                        bias_initializer=zeros())(pool2)  # "One conv at the beginning (spatial size: 32x32)"
        if enable_bn: conv3 = BatchNormalization(axis=self._channel_axis, momentum=0.9997)(conv3)
        pool3 = MaxPooling2D(pool_size=3, strides=2)(conv3)

        flatten = Flatten()(pool3)

        full1 = Dense(512,  kernel_regularizer=l2(self._weight_decay),
                            bias_initializer=ones(),
                            kernel_initializer=random_normal(stddev=0.005))(flatten)
        drop1 = Dropout(rate=pkeep)(full1)
        full2 = Dense(512,  kernel_regularizer=l2(self._weight_decay),
                            bias_initializer=ones(),
                            kernel_initializer=random_normal(stddev=0.005))(drop1)
        drop2 = Dropout(rate=pkeep)(full2)

        predictions_g = Dense(units=2, kernel_initializer=random_normal(stddev=0.01), bias_initializer=zeros(), name="Gender_Prediction",
                              activation="softmax")(drop2)
        predictions_a = Dense(units=101, kernel_initializer=random_normal(stddev=0.01), bias_initializer=zeros(), name="Age_Prediction",
                              activation="softmax")(drop2)

        model = Model(inputs=inputs, outputs=[predictions_g, predictions_a])

        return model

    def predict(self, face_imgs):
        results = self.model.predict(face_imgs)
        predicted_genders = results[0]
        predicted_ages = results[1].dot(self._ages).flatten()

        return predicted_genders, predicted_ages