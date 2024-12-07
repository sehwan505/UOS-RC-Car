# -*- coding: utf-8 -*-
import socket
import sys
import os
import numpy as np
import pdb
import serial

import cv2
import time
from picamera2 import Picamera2

from Image import *
from Utils import *

WIDTH = 320
HEIGHT = 240
TOLERANCE = 140
TURN_MAX = 190
TURN_MID = 90

font = cv2.FONT_HERSHEY_SIMPLEX
direction = 0

Images = []
N_SLICES = 6

#ser = serial.Serial("/dev/serial/by-id/usb-Arduino_Srl_Arduino_Uno_754393137373514170C0-if00", 9600)

print("start")
time.sleep(3)

for q in range(N_SLICES):
    Images.append(Image())


def in_tolerance(n):
    if n < -TOLERANCE:
        return False
    if n > TOLERANCE:
        return False
    return True


def get_direction(y1, y2, y3, y4, y5, y6):

    num_valid = 6
    y1 -= WIDTH / 2
    y2 -= WIDTH / 2
    y3 -= WIDTH / 2
    y4 -= WIDTH / 2
    y5 -= WIDTH / 2
    y6 -= WIDTH / 2
    print("y1:%d, y2:%d, y3:%d, y4:%d, y5:%d, y6:%d" % (y1, y2, y3, y4, y5, y6))
    master_point = 0
    
    # +: right
    # -: left
    if in_tolerance(y1) == False:
        num_valid -= 1
        y1 = 0
    if in_tolerance(y2) == False:
        num_valid -= 1
        y2 = 0
    if in_tolerance(y3) == False:
        num_valid -= 1
        y3 = 0
    if in_tolerance(y4) == False:
        num_valid -= 1
        y4 = 0
    if in_tolerance(y5) == False:
        num_valid -= 1
        y5 = 0
    if in_tolerance(y6) == False:
        num_valid -= 1
        y6 = 0

    master_point = (
        2.65
        * (y1 * 0.7 + y2 * 0.85 + y3 + y4 * 1.1 + y5 * 1.2 + y6 * 1.35)
        / (num_valid + 0.1)
    )
    #master_point += y1 * 0.5
    #master_point += y2 * 0.4
    #master_point += y3 * 0.3
    #master_point -= y4 * 0.4
    #master_point -= y5 * 0.5
    #master_point -= y6 * 0.6

    print(master_point)

    direction = "F"
    if master_point > TURN_MID and master_point < TURN_MAX:
        direction = "r"
    if master_point < -TURN_MID and master_point > -TURN_MAX:
        direction = "l"
    if master_point >= TURN_MAX:
        direction = "R"
    if master_point <= -TURN_MAX:
        direction = "L"

    cmd = ("%c\n" % (direction)).encode("ascii")

    print(">>> master_point:%d, cmd:%s" % (master_point, cmd))

    ser.write(cmd)
    print("send")
    time.sleep(1)
    read_serial = ser.readline()
    print("<<< %s" % (read_serial))


# Picamera2 설정
picam2 = Picamera2()
camera_config = picam2.create_still_configuration(
    main={"format": "BGR888", "size": (WIDTH, HEIGHT)}
)
picam2.configure(camera_config)
picam2.start()

# 카메라 워밍업 시간
time.sleep(0.1)

skip = 30
while True:
    fram = picam2.capture_array()
    if skip > 0:
        skip -= 1
    elif fram is not None:
        skip = 6
        # 이미지를 조각내서 윤곽선을 표시하게 무게중심 점을 얻는다
        Points = SlicePart(fram, Images, N_SLICES)
        print("Points : ", Points)
        fm = RepackImages(Images)
        output_path = f"output_image.jpg"
        cv2.imwrite(output_path, fm)
        # command
        #get_direction(
        #    Points[0][0],
        #    Points[1][0],
        #    Points[2][0],
        #    Points[3][0],
        #    Points[4][0],
        #    Points[5][0],
        #)

    else:
        print("not even processed")
