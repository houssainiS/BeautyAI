import cv2
import numpy as np
from PIL import Image
import mediapipe as mp

mp_face_mesh = mp.solutions.face_mesh

def detect_and_crop_face(pil_image: Image.Image) -> Image.Image:
    """
    Detect face using MediaPipe Face Mesh, crop tight face box, return PIL image.
    Raises ValueError if no face or multiple faces detected.
    """
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

        # Extract all landmark points x and y in pixels
        xs = [int(lm.x * w) for lm in landmarks]
        ys = [int(lm.y * h) for lm in landmarks]

        # Get bounding box of landmarks with a margin
        x_min, x_max = max(min(xs) - 20, 0), min(max(xs) + 20, w)
        y_min, y_max = max(min(ys) - 20, 0), min(max(ys) + 20, h)

        face_crop = image[y_min:y_max, x_min:x_max]
        return Image.fromarray(face_crop)

def crop_left_eye(pil_image: Image.Image) -> Image.Image:
    """
    Crop the left eye (person's right eye in the image).
    """
    return _crop_eye(pil_image, eye_indices=[
        33, 133, 160, 159, 158, 144, 153, 154, 155, 133
    ])

def crop_right_eye(pil_image: Image.Image) -> Image.Image:
    """
    Crop the right eye (person's left eye in the image).
    """
    return _crop_eye(pil_image, eye_indices=[
        362, 263, 387, 386, 385, 373, 380, 381, 382, 362
    ])

def _crop_eye(pil_image: Image.Image, eye_indices: list) -> Image.Image:
    """
    Helper function to crop eye region based on given landmark indices.
    """
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
