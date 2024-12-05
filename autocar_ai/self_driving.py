__author__ = "will"

from .rc_car_interface import RC_Car_Interface
from .tf_learn import DNN_Driver
import numpy as np
import time
import cv2


class SelfDriving:

    def __init__(self):
        self.rc_car_cntl = RC_Car_Interface()
        self.dnn_driver = DNN_Driver()

        self.velocity = 0
        self.direction = 0

        self.dnn_driver.tf_learn()

    def rc_car_control(self, direction):
        if direction < -0.3:
            self.rc_car_cntl.set_direction("L")
        elif direction > 0.3:
            self.rc_car_cntl.set_direction("R")
        else:
            self.rc_car_cntl.set_direction("F")

    def drive(self):
        while True:
            img = self.rc_car_cntl.get_image_from_camera()
            img = np.reshape(img, img.shape[0] ** 2)

            direction = self.dnn_driver.predict_direction(img)
            self.rc_car_control(direction[0][0])

            time.sleep(0.001)

        self.rc_car_cntl.stop()
        cv2.destroyAllWindows()


SelfDriving().drive()
