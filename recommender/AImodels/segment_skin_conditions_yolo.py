# recommender/AImodels/segment_skin_conditions_yolo.py
from ultralytics import YOLO
import numpy as np
import cv2
from PIL import Image
import gc
import torch

# ----------------------
# Load segmentation YOLO model once
# ----------------------
SEG_MODEL_PATH = "recommender/AImodels/skin_condition_seg.pt"
seg_model = YOLO(SEG_MODEL_PATH)

# ----------------------
# Segment skin conditions
# ----------------------
def segment_skin_conditions(image_pil: Image.Image, conf_threshold=0.3):
    """
    Run YOLO segmentation on the input PIL image.
    Returns:
        - image_pil_result: PIL.Image with segmentation overlay
        - segmentation_results: list of dicts {'label': str, 'confidence': float}
    """
    image_np = None
    image_bgr = None
    results = None
    image_result = None
    image_pil_result = None
    
    try:
        # Convert PIL to OpenCV
        image_np = np.array(image_pil)
        image_bgr = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)

        # Run inference (single image, no streaming for memory efficiency)
        results = seg_model.predict(source=image_bgr, conf=conf_threshold, stream=False)[0]

        # Overlay masks and results
        image_result = results.plot()

        # Convert back to PIL for Django
        image_pil_result = Image.fromarray(cv2.cvtColor(image_result, cv2.COLOR_BGR2RGB))

        # Extract detected classes + confidence scores
        segmentation_results = []
        if hasattr(results, "boxes") and results.boxes is not None:
            for box in results.boxes:
                cls_id = int(box.cls[0].item())
                conf = float(box.conf[0].item())
                label = results.names[cls_id] if results.names else str(cls_id)
                segmentation_results.append({
                    "label": label,
                    "confidence": round(conf, 4)
                })

        return image_pil_result, segmentation_results
        
    finally:
        # Clean up all intermediate objects
        if image_np is not None:
            del image_np
        if image_bgr is not None:
            del image_bgr
        if image_result is not None:
            del image_result
        if results is not None:
            del results
            
        # Clear CUDA cache if using GPU
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            
        # Force garbage collection
        gc.collect()
