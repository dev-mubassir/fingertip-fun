# Fingertip Fun 

Interactive hand-tracking overlays using MediaPipe and OpenCV. Control polygons with your fingertips — no clicks, no pins, just hands.

## Demo

| Script | Description |
|--------|-------------|
| `hand_fingertip_overlay.py` | **Main demo** — All visible fingertips (both hands) form one convex polygon with grayscale fill |
| `hand_gesture_overlay.py` | Pinch (thumb+index) to add/drag vertices |
| `dynamic_overlay.py` | Mouse-controlled version (click to add, drag to move) |

## Requirements

- Python 3.8+
- Webcam
- `opencv-python`, `mediapipe`, `numpy`

```bash
pip install opencv-python mediapipe numpy
```

## Quick Start

```bash
# Main fingertip tracking (recommended)
python hand_fingertip_overlay.py

# Pinch gesture version
python hand_gesture_overlay.py

# Mouse version
python dynamic_overlay.py
```

## Controls

| Key | Action |
|-----|--------|
| `q` / `ESC` | Quit |
| `c` | Clear points (gesture/mouse versions only) |

## How It Works

### `hand_fingertip_overlay.py`
- Detects up to 2 hands via MediaPipe HandLandmarker
- Tracks **all 5 fingertips per hand** (thumb, index, middle, ring, pinky)
- Combines all visible fingertips into a **single convex hull**
- Fills polygon with **grayscale** (desaturated camera feed)
- Draws **thin black & white outline** for contrast

### `hand_gesture_overlay.py`
- Pinch thumb + index → add vertex or grab nearest
- Release pinch → drop vertex
- Index finger shows cursor with green ring when pinching

### `dynamic_overlay.py`
- Left-click empty space → add vertex
- Click vertex → drag to move
- Green lines connect vertices, yellow semi-transparent fill (3+ points)

## Model

Uses MediaPipe's `hand_landmarker.task` (included). Downloaded from:
```
https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task
```

## Project Structure

```
fingertip-fun/
├── hand_fingertip_overlay.py   # Main: all fingertips → one polygon
├── hand_gesture_overlay.py     # Pinch to add/drag vertices
├── dynamic_overlay.py          # Mouse version
├── hand_landmarker.task        # MediaPipe model
└── README.md
```

## Troubleshooting

**Webcam not found**: Change `cv2.VideoCapture(0)` to `1` or `2` for external cameras.

**MediaPipe warnings**: The `W0000` logs are normal TensorFlow Lite initialization noise.

**Slow performance**: Ensure good lighting; MediaPipe runs on CPU by default.

## License

MIT — do whatever you want with it.
