# recommender/AImodels/segment_skin_conditions_yolo.py
from ultralytics import YOLO
import numpy as np
import cv2
from PIL import Image

# Load model once (on import)
seg_model = YOLO("recommender/AImodels/skin_condition_seg.pt")

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

    # Extract classes + confidence scores
    segmentation_results = []
    if hasattr(results[0], "boxes") and results[0].boxes is not None:
        for box in results[0].boxes:
            cls_id = int(box.cls[0].item())
            conf = float(box.conf[0].item())
            label = results[0].names[cls_id] if results[0].names else str(cls_id)
            segmentation_results.append({
                "label": label,
                "confidence": round(conf, 4)
            })

    return image_pil_result, segmentation_results
