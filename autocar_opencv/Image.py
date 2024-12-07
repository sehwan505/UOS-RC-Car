# -*- coding: utf-8 -*-
import numpy as np
import cv2


class Image:

    def __init__(self):
        self.image = None
        self.contourCenterX = 0
        self.MainContour = None

    def single_scale_retinex(self, channel, sigma=15):
        # float 변환 및 로그 영역으로 이동
        img = channel.astype(np.float32) + 1.0
        log_img = np.log(img)

        # 가우시안 블러를 이용해 조명성분 추정
        blur = cv2.GaussianBlur(img, (0, 0), sigma)
        log_blur = np.log(blur)

        # 반사 성분 = 로그(원본) - 로그(조명)
        retinex = log_img - log_blur
        return retinex

    def retinex_enhancement(self, bgr_img, sigma=15):
        # BGR 채널 각각에 SSR 적용
        b, g, r = cv2.split(bgr_img)
        b_ret = self.single_scale_retinex(b, sigma)
        g_ret = self.single_scale_retinex(g, sigma)
        r_ret = self.single_scale_retinex(r, sigma)

        merged = cv2.merge([b_ret, g_ret, r_ret])
        exp_img = np.exp(merged)  # exp로 복원
        exp_img = exp_img - np.min(exp_img)
        exp_img = exp_img / np.max(exp_img) * 255.0
        exp_img = np.clip(exp_img, 0, 255).astype(np.uint8)
        return exp_img

    def minimize_light_effect_for_black_line(self, image, use_retinex=True):
        # 조명 보정
        if use_retinex:
            processed = self.retinex_enhancement(image, sigma=15)
        else:
            processed = image

        # 그레이 변환
        imgray = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)

        # Top-hat 변환으로 국소 명암 보정 (선 강조)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
        tophat = cv2.morphologyEx(imgray, cv2.MORPH_TOPHAT, kernel)

        # 정규화
        normalized = cv2.normalize(tophat, None, 0, 255, cv2.NORM_MINMAX)

        # Otsu 이진화(검정 선을 찾기 위해 INV 사용)
        _, thresh = cv2.threshold(
            normalized, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
        )

        # Morphological 연산으로 선 정제
        kernel_line = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        clean_line = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel_line)

        return clean_line

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
