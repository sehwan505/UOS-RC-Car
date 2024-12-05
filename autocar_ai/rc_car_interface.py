# Copyright(c) Reserved 2020.
# Donghee Lee, University of Soul
#
__author__ = "will"

import numpy as np
import cv2
import serial
from picamera2 import PiCamera2


class RC_Car_Interface:

    def __init__(self, arduino_port="/dev/ttyACM0"):
        self.camera = PiCamera2()
        camera_config = self.camera.create_still_configuration(
            main={"size": (320, 320)}
        )
        self.camera.configure(camera_config)
        self.camera.start()
        self.serial = serial.Serial(arduino_port, 9600)

    def set_direction(self, direction):
        self.serial.write(direction + "\n").encode("ascii")
        # while self.serial.in_waiting == 0:
        #     pass

    def get_image_from_camera(self):
        img = np.empty((320, 320, 3), dtype=np.uint8)
        self.camera.capture(img, "bgr")
        img = img[:, :, 0]

        threshold = int(np.mean(img)) * 0.5
        ret, img2 = cv2.threshold(
            img.astype(np.uint8), threshold, 255, cv2.THRESH_BINARY_INV
        )

        img2 = cv2.resize(img2, (16, 16), interpolation=cv2.INTER_AREA)
        return img2

    def stop(self):
        print("stop")
