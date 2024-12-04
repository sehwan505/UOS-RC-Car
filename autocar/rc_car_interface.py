# Copyright(c) Reserved 2020.
# Donghee Lee, University of Soul
#
__author__ = "will"

import numpy as np
import cv2

from picamera.array import PiRGBArray
from picamera import PiCamera


class RC_Car_Interface:

    def __init__(self):
        self.left_wheel = 0
        self.right_wheel = 0
        self.camera = PiCamera()
        self.camera.resolution = (320, 320)
        self.camera.color_effects = (128, 128)

    def finish_iteration(self):
        print("finish iteration")

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

    def stop(self):  # robot stop
        print("stop")


# Test Only
# RC_Car_Interface().get_image_from_camera()
