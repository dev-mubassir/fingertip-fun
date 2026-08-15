import cv2
import numpy as np


class DynamicOverlay:
    def __init__(self):
        self.points = []
        self.dragging_index = None
        self.drag_threshold = 15
        self.window_name = 'Dynamic Coordinate Overlay'
        self.cap = None

    def find_vertex_near(self, x, y):
        for i, (px, py) in enumerate(self.points):
            if (x - px) ** 2 + (y - py) ** 2 <= self.drag_threshold ** 2:
                return i
        return None

    def mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            idx = self.find_vertex_near(x, y)
            if idx is not None:
                self.dragging_index = idx
            else:
                self.points.append([x, y])

        elif event == cv2.EVENT_MOUSEMOVE:
            if self.dragging_index is not None:
                self.points[self.dragging_index] = [x, y]

        elif event == cv2.EVENT_LBUTTONUP:
            self.dragging_index = None

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
            cv2.circle(frame, (x, y), 8, color, -1)
            cv2.circle(frame, (x, y), 8, (255, 255, 255), 2)
            self.draw_coordinate_label(frame, x, y)

        return frame

    def run(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Error: Could not open webcam.")
            return

        cv2.namedWindow(self.window_name)
        cv2.setMouseCallback(self.window_name, self.mouse_callback)

        print("Dynamic Coordinate Overlay started.")
        print("Controls:")
        print("  Left-click: Add vertex")
        print("  Drag vertex: Move existing vertex")
        print("  'c': Clear all points")
        print("  'q' or ESC: Quit")

        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Error: Failed to read frame.")
                break

            frame = cv2.flip(frame, 1)
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
    app = DynamicOverlay()
    app.run()