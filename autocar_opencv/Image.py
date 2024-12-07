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

    def minimize_light_effect(self, image, use_retinex=True):
        if use_retinex:
            processed = self.retinex_enhancement(image, sigma=15)
        else:
            processed = image

        # 그레이 변환
        imgray = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)

        # Black-hat 변환으로 어두운 선 강조
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
        blackhat = cv2.morphologyEx(imgray, cv2.MORPH_BLACKHAT, kernel)

        # 정규화
        normalized = cv2.normalize(blackhat, None, 0, 255, cv2.NORM_MINMAX)

        # Otsu 이진화 (검은 선이 강조되어 흰색으로 표현될 경우, 일반 THRESH_BINARY 사용)
        _, thresh = cv2.threshold(
            normalized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )
        cv2.imshow("Thresh.jpg", thresh)
        return thresh

    def calculateAverageCenter(self, contours):
        total_x, total_y = 0, 0
        valid_contours = 0

        for contour in contours:
            center = self.getContourCenter(contour)
            if center != 0:
                total_x += center[0]
                total_y += center[1]
                valid_contours += 1

        if valid_contours > 0:
            avg_x = total_x // valid_contours
            avg_y = total_y // valid_contours
            return [avg_x, avg_y]
        else:
            return [0, 0]

    def Process(self):
        thresh = self.minimize_light_effect(self.image)
        self.contours, _ = cv2.findContours(
            thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
        )

        if self.contours:
            # 모든 윤곽의 평균 중심 계산
            self.contourCenterX, self.contourCenterY = self.calculateAverageCenter(
                self.contours
            )

            # 이미지 크기 가져오기
            self.height, self.width = self.image.shape[:2]
            if len(contour_centers) > 1:  # 중심점이 2개 이상일 때만 분포 확인
                # 중심점들의 Bounding Box 계산
                contour_centers = np.array(contour_centers)
                distances = np.linalg.norm(
                    contour_centers[:, None] - contour_centers, axis=2
                )
                std_distance = np.std(distances)

                # 기준: Bounding Box가 화면의 70% 이상이거나, 중심점 간 거리 분포가 넓으면 산재로 간주
                if std_distance > 0.2 * self.width:
                    self.contourCenterX, self.contourCenterY = 0, 0  # Invalid 상태
                    print("invalid white")
                    return [self.contourCenterX, self.middleY], self.image

            # 이미지 중앙 좌표 계산
            self.middleX = int(self.width / 2)
            self.middleY = int(self.height / 2)

            # 윤곽선 그리기: 초록색
            cv2.drawContours(self.image, self.contours, -1, (0, 255, 0), 1)

            # 중심점 그리기: 흰색
            cv2.circle(
                self.image,
                (self.contourCenterX, self.contourCenterY),
                7,
                (255, 255, 255),
                -1,
            )

            # 이미지 중앙점 그리기: 빨간색
            cv2.circle(self.image, (self.middleX, self.middleY), 3, (0, 0, 255), -1)

            # 텍스트 추가
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(
                self.image,
                str(self.middleX - self.contourCenterX),
                (self.contourCenterX + 20, self.contourCenterY),
                font,
                1,
                (200, 0, 200),
                2,
                cv2.LINE_AA,
            )
        else:
            # 윤곽이 없는 경우 초기값 반환
            self.contourCenterX, self.contourCenterY = 0, 0

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
