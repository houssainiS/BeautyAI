import cv2
import numpy as np
from PIL import Image
import mediapipe as mp

mp_face_mesh = mp.solutions.face_mesh

def detect_and_crop_face(pil_image: Image.Image):
    """
    Detect face, check lighting and tilt, and check if eyes are closed.
    Returns (cropped_face: PIL.Image, left_closed: bool, right_closed: bool)
    Raises ValueError only if lighting is poor or no face found.
    """
    image = np.array(pil_image.convert("RGB"))
    h, w, _ = image.shape

    # Brightness check
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    center_x, center_y = w // 2, h // 2
    sample_size = 100
    x1 = max(center_x - sample_size // 2, 0)
    y1 = max(center_y - sample_size // 2, 0)
    x2 = min(center_x + sample_size // 2, w)
    y2 = min(center_y + sample_size // 2, h)

    face_region = gray[y1:y2, x1:x2]
    brightness = np.mean(face_region)

    if brightness < 50:
        raise ValueError("Poor lighting detected. Please use a well-lit photo.")

    with mp_face_mesh.FaceMesh(
        static_image_mode=True,
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5
    ) as face_mesh:
        results = face_mesh.process(image)

        if not results.multi_face_landmarks or len(results.multi_face_landmarks) != 1:
            raise ValueError("Please upload a clear photo with exactly one face.")

        landmarks = results.multi_face_landmarks[0].landmark

        # Eye closed check
        def is_eye_closed(indices):
            pts = np.array([(landmarks[i].x * w, landmarks[i].y * h) for i in indices])
            vertical = np.linalg.norm(pts[1] - pts[5]) + np.linalg.norm(pts[2] - pts[4])
            horizontal = np.linalg.norm(pts[0] - pts[3])
            ratio = vertical / (2.0 * horizontal)
            return ratio < 0.20

        left_eye_indices = [362, 385, 387, 263, 373, 380]
        right_eye_indices = [33, 160, 158, 133, 153, 144]

        left_closed = is_eye_closed(left_eye_indices)
        right_closed = is_eye_closed(right_eye_indices)

        # Tilt check — soft warning
        def get_eye_center(indices):
            pts = np.array([(landmarks[i].x * w, landmarks[i].y * h) for i in indices])
            return np.mean(pts, axis=0)

        left_center = get_eye_center(left_eye_indices)
        right_center = get_eye_center(right_eye_indices)

        dx = right_center[0] - left_center[0]
        dy = right_center[1] - left_center[1]
        angle = np.degrees(np.arctan2(dy, dx))

        if abs(angle) > 30:
            print(f"[WARN] Face tilt angle too high: {angle:.1f} degrees")

        # Crop face tightly
        xs = [int(lm.x * w) for lm in landmarks]
        ys = [int(lm.y * h) for lm in landmarks]
        x_min, x_max = max(min(xs) - 20, 0), min(max(xs) + 20, w)
        y_min, y_max = max(min(ys) - 20, 0), min(max(ys) + 20, h)

        face_crop = image[y_min:y_max, x_min:x_max]
        return Image.fromarray(face_crop), left_closed, right_closed


def crop_left_eye(pil_image: Image.Image) -> Image.Image:
    return _crop_eye(pil_image, eye_indices=[
        33, 133, 160, 159, 158, 144, 153, 154, 155, 133
    ])

def crop_right_eye(pil_image: Image.Image) -> Image.Image:
    return _crop_eye(pil_image, eye_indices=[
        362, 263, 387, 386, 385, 373, 380, 381, 382, 362
    ])

def _crop_eye(pil_image: Image.Image, eye_indices: list) -> Image.Image:
    image = np.array(pil_image.convert("RGB"))
    h, w, _ = image.shape

    with mp_face_mesh.FaceMesh(
        static_image_mode=True,
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5
    ) as face_mesh:
        results = face_mesh.process(image)

        if not results.multi_face_landmarks or len(results.multi_face_landmarks) != 1:
            raise ValueError("Please upload a clear photo with exactly one face.")

        landmarks = results.multi_face_landmarks[0].landmark
        eye_points = [(int(landmarks[i].x * w), int(landmarks[i].y * h)) for i in eye_indices]

        xs, ys = zip(*eye_points)
        x_min, x_max = max(min(xs) - 10, 0), min(max(xs) + 10, w)
        y_min, y_max = max(min(ys) - 10, 0), min(max(ys) + 10, h)

        eye_crop = image[y_min:y_max, x_min:x_max]
        return Image.fromarray(eye_crop)
