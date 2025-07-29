# recommender/models/segment_skin_conditions_yolo.py
from ultralytics import YOLO
import numpy as np
import cv2
from PIL import Image

# Load model once (on import)
seg_model = YOLO("C:/Users/Slimen/Desktop/tets 3 seg/skin_condition_seg.pt")

def segment_skin_conditions(image_pil):
    # Convert PIL to OpenCV
    image_np = np.array(image_pil)
    image_bgr = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)

    # Run inference
    results = seg_model.predict(image_bgr)

    # Overlay masks and results
    image_result = results[0].plot()

    # Convert back to PIL for Django
    image_result_rgb = cv2.cvtColor(image_result, cv2.COLOR_BGR2RGB)
    image_pil_result = Image.fromarray(image_result_rgb)

    return image_pil_result, results[0]
