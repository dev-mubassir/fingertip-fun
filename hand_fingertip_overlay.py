import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


class HandFingertipOverlay:
    def __init__(self):
        self.window_name = 'Hand Fingertip Overlay'
        self.cap = None
        self.fingertip_indices = [4, 8, 12, 16, 20]

        base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_hands=2,
            min_hand_detection_confidence=0.7,
            min_hand_presence_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.landmarker = vision.HandLandmarker.create_from_options(options)

    def get_fingertips(self, landmarks, w, h):
        points = []
        for idx in self.fingertip_indices:
            lm = landmarks[idx]
            x, y = int(lm.x * w), int(lm.y * h)
            points.append([x, y])
        return np.array(points, dtype=np.int32)

    def apply_grayscale_fill(self, frame, points):
        if len(points) < 3:
            return frame
        
        mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        cv2.fillPoly(mask, [points], 255)
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        
        frame[mask == 255] = gray_bgr[mask == 255]
        return frame

    def draw_thin_polygon(self, frame, points):
        if len(points) < 2:
            return frame
        
        cv2.polylines(frame, [points], isClosed=True, color=(0, 0, 0), thickness=3)
        cv2.polylines(frame, [points], isClosed=True, color=(255, 255, 255), thickness=1)
        return frame

    def draw_fingertips(self, frame, points):
        for x, y in points:
            cv2.circle(frame, (x, y), 6, (0, 0, 0), -1)
            cv2.circle(frame, (x, y), 6, (255, 255, 255), 1)
        return frame

    def run(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Error: Could not open webcam.")
            return

        cv2.namedWindow(self.window_name)

        print("Hand Fingertip Overlay started.")
        print("Show hands - all 5 fingertips tracked per hand")
        print("Polygon formed by fingertips, filled with grayscale")
        print("'q' or ESC: Quit")

        timestamp_ms = 0

        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Error: Failed to read frame.")
                break

            frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
            timestamp_ms += 33
            results = self.landmarker.detect_for_video(mp_image, timestamp_ms)

            all_fingertips = []

            if results.hand_landmarks:
                for hand_landmarks in results.hand_landmarks:
                    fingertips = self.get_fingertips(hand_landmarks, w, h)
                    all_fingertips.append(fingertips)

            if all_fingertips:
                combined = np.vstack(all_fingertips)
                if len(combined) >= 3:
                    hull = cv2.convexHull(combined)
                    frame = self.apply_grayscale_fill(frame, hull)
                    frame = self.draw_thin_polygon(frame, hull)
                for fingertips in all_fingertips:
                    frame = self.draw_fingertips(frame, fingertips)

            cv2.imshow(self.window_name, frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                break

        self.cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    app = HandFingertipOverlay()
    app.run()