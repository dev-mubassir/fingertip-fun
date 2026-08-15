import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


class HandGestureOverlay:
    def __init__(self):
        self.points = []
        self.dragging_index = None
        self.drag_threshold = 40
        self.pinch_threshold = 30
        self.window_name = 'Hand Gesture Overlay'
        self.cap = None
        self.prev_pinch = False
        self.pinch_cooldown = 0

        base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_hands=1,
            min_hand_detection_confidence=0.7,
            min_hand_presence_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.landmarker = vision.HandLandmarker.create_from_options(options)

    def find_vertex_near(self, x, y):
        for i, (px, py) in enumerate(self.points):
            if (x - px) ** 2 + (y - py) ** 2 <= self.drag_threshold ** 2:
                return i
        return None

    def is_pinch(self, landmarks):
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        dist = np.sqrt((thumb_tip.x - index_tip.x) ** 2 + (thumb_tip.y - index_tip.y) ** 2)
        return dist < 0.05

    def get_index_finger_pos(self, landmarks, w, h):
        index_tip = landmarks[8]
        return int(index_tip.x * w), int(index_tip.y * h)

    def draw_coordinate_label(self, frame, x, y):
        label = f"x: {x} y: {y}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        thickness = 1
        (tw, th), _ = cv2.getTextSize(label, font, font_scale, thickness)

        h, w = frame.shape[:2]
        bg_x1 = min(max(x + 12, 0), w - tw - 16)
        bg_y1 = max(y - th - 8, 0)
        bg_x2 = bg_x1 + tw + 4
        bg_y2 = min(y + 4, h)

        cv2.rectangle(frame, (bg_x1, bg_y1), (bg_x2, bg_y2), (0, 0, 0), -1)
        cv2.putText(frame, label, (bg_x1 + 2, y), font, font_scale, (255, 255, 255), thickness)

    def render(self, frame):
        h, w = frame.shape[:2]

        if len(self.points) >= 3:
            overlay = frame.copy()
            pts = np.array(self.points, dtype=np.int32).reshape((-1, 1, 2))
            cv2.fillPoly(overlay, [pts], color=(0, 255, 255))
            cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)

        if len(self.points) >= 2:
            pts = np.array(self.points, dtype=np.int32).reshape((-1, 1, 2))
            cv2.polylines(frame, [pts], isClosed=False, color=(0, 255, 0), thickness=2)

        for i, (x, y) in enumerate(self.points):
            color = (0, 0, 255) if i == self.dragging_index else (255, 0, 255)
            cv2.circle(frame, (x, y), 10, color, -1)
            cv2.circle(frame, (x, y), 10, (255, 255, 255), 2)
            self.draw_coordinate_label(frame, x, y)

        return frame

    def run(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Error: Could not open webcam.")
            return

        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        print("Hand Gesture Overlay started.")
        print("Gestures:")
        print("  Pinch (thumb + index): Add vertex / Start drag")
        print("  Release pinch: Drop vertex")
        print("  'c': Clear all points")
        print("  'q' or ESC: Quit")

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

            index_pos = None
            pinch = False

            if results.hand_landmarks:
                landmarks = results.hand_landmarks[0]
                index_pos = self.get_index_finger_pos(landmarks, w, h)
                pinch = self.is_pinch(landmarks)

                cx, cy = index_pos
                cv2.circle(frame, (cx, cy), 12, (255, 0, 255), -1)
                cv2.circle(frame, (cx, cy), 12, (255, 255, 255), 2)

                if pinch:
                    cv2.circle(frame, (cx, cy), 20, (0, 255, 0), 3)

            if pinch and not self.prev_pinch and self.pinch_cooldown == 0:
                if self.dragging_index is None:
                    idx = self.find_vertex_near(index_pos[0], index_pos[1])
                    if idx is not None:
                        self.dragging_index = idx
                    else:
                        self.points.append(list(index_pos))
                self.pinch_cooldown = 10

            if not pinch and self.prev_pinch:
                self.dragging_index = None

            if self.dragging_index is not None and index_pos:
                self.points[self.dragging_index] = list(index_pos)

            if self.pinch_cooldown > 0:
                self.pinch_cooldown -= 1

            self.prev_pinch = pinch

            frame = self.render(frame)

            cv2.imshow(self.window_name, frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                break
            elif key == ord('c'):
                self.points.clear()
                self.dragging_index = None

        self.cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    app = HandGestureOverlay()
    app.run()