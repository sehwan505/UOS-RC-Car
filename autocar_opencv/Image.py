# -*- coding: utf-8 -*-
import numpy as np
import cv2


class Image:

    def __init__(self):
        self.image = None
        self.contourCenterX = 0
        self.MainContour = None

    def minimize_light_effect(self, image):
        imgray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        imgray = clahe.apply(imgray)
        imgray = cv2.GaussianBlur(imgray, (5, 5), 0)

        dilated_img = cv2.dilate(imgray, np.ones((15, 15), np.uint8))
        bg_img = cv2.medianBlur(dilated_img, 21)
        diff_img = 255 - cv2.absdiff(imgray, bg_img)
        imgray = cv2.normalize(
            diff_img, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX
        )
        thresh = cv2.adaptiveThreshold(
            imgray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
        )

        return thresh

    def Process(self):
        # 이미지를 흑백으로 변환한 뒤 Threshold 값을 기준으로 0 또는 1로 값을 정한다
        thresh = self.minimize_light_effect(self.image)
        self.contours, _ = cv2.findContours(
            thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
        )

        self.prev_MC = self.MainContour
        if self.contours:
            self.MainContour = max(self.contours, key=cv2.contourArea)

            self.height, self.width = self.image.shape[:2]

            self.middleX = int(self.width / 2)
            self.middleY = int(self.height / 2)

            self.prev_cX = self.contourCenterX
            if self.getContourCenter(self.MainContour) != 0:
                self.contourCenterX = self.getContourCenter(self.MainContour)[0]
                if abs(self.prev_cX - self.contourCenterX) > 5:
                    self.correctMainContour(self.prev_cX)
            else:
                self.contourCenterX = 0

            self.dir = int(
                (self.middleX - self.contourCenterX)
                * self.getContourExtent(self.MainContour)
            )

            # 윤곽선은 초록색, 무게중심은 흰색 원, 그림의 중앙 지점은 빨간 원으로 표시
            cv2.drawContours(
                self.image, self.MainContour, -1, (0, 255, 0), 3
            )  # Draw Contour GREEN
            cv2.circle(
                self.image, (self.contourCenterX, self.middleY), 7, (255, 255, 255), -1
            )  # Draw dX circle WHITE
            cv2.circle(
                self.image, (self.middleX, self.middleY), 3, (0, 0, 255), -1
            )  # Draw middle circle RED

            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(
                self.image,
                str(self.middleX - self.contourCenterX),
                (self.contourCenterX + 20, self.middleY),
                font,
                1,
                (200, 0, 200),
                2,
                cv2.LINE_AA,
            )
            cv2.putText(
                self.image,
                "Weight:%.3f" % self.getContourExtent(self.MainContour),
                (self.contourCenterX + 20, self.middleY + 35),
                font,
                0.5,
                (200, 0, 200),
                1,
                cv2.LINE_AA,
            )
        return [self.contourCenterX, self.middleY], self.image

    def getContourCenter(self, contour):
        M = cv2.moments(contour)

        if M["m00"] == 0:
            return 0

        x = int(M["m10"] / M["m00"])
        y = int(M["m01"] / M["m00"])

        return [x, y]

    def getContourExtent(self, contour):
        area = cv2.contourArea(contour)
        x, y, w, h = cv2.boundingRect(contour)
        rect_area = w * h
        if rect_area > 0:
            return float(area) / rect_area

    def Aprox(self, a, b, error):
        if abs(a - b) < error:
            return True
        else:
            return False

    def correctMainContour(self, prev_cx):
        if abs(prev_cx - self.contourCenterX) > 5:
            for i in range(len(self.contours)):
                if self.getContourCenter(self.contours[i]) != 0:
                    tmp_cx = self.getContourCenter(self.contours[i])[0]
                    if self.Aprox(tmp_cx, prev_cx, 5) == True:
                        self.MainContour = self.contours[i]
                        if self.getContourCenter(self.MainContour) != 0:
                            self.contourCenterX = self.getContourCenter(
                                self.MainContour
                            )[0]
