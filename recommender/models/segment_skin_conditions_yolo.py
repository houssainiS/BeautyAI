# recommender/models/segment_skin_conditions_yolo.py
def get_seg_model():
    # Lazy import
    from ultralytics import YOLO
    import os

    # You can adjust the model path to use relative or Render-compatible paths
    model_path = "C:/Users/Slimen/Desktop/tets 3 seg/skin_condition_seg.pt"

    if not hasattr(get_seg_model, "_model"):
        get_seg_model._model = YOLO(model_path)
    return get_seg_model._model


def segment_skin_conditions(image_pil):
    # Lazy imports
    import numpy as np
    import cv2
    from PIL import Image

    # Convert PIL to OpenCV
    image_np = np.array(image_pil)
    image_bgr = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)

    # Run inference
    model = get_seg_model()
    results = model.predict(image_bgr)

    # Overlay masks and results
    image_result = results[0].plot()

    # Convert back to PIL for Django
    image_result_rgb = cv2.cvtColor(image_result, cv2.COLOR_BGR2RGB)
    image_pil_result = Image.fromarray(image_result_rgb)

    return image_pil_result, results[0]
