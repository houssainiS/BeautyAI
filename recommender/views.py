from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from PIL import Image
import base64
import io
import json
import gc  # Added garbage collection import

from recommender.AImodels.ml_model import predict
from recommender.AImodels.yolo_model import detect_skin_defects_yolo
from recommender.AImodels.segment_skin_conditions_yolo import segment_skin_conditions  # updated to return structured results

# NEW: import tips dictionaries
from recommender.tips import SKIN_TYPE_TIPS, EYE_COLOR_TIPS, ACNE_TIPS, SEGMENTATION_TIPS, YOLO_TIPS

from .models import FaceAnalysis, Feedback


def home(request):
    """
    Render the homepage.
    """
    return render(request, "recommender/home.html")


@csrf_exempt
def upload_photo(request):
    """
    Handle POST requests with an uploaded photo or base64 image string.
    Run multiple AI models to analyze skin type, acne, eye colors, skin defects,
    and segmentation. Returns a detailed JSON response with results and images.

    Also logs a FaceAnalysis record for each successful analysis to count usage.
    """
    if request.method == "POST":
        image = None
        cropped_face = None
        yolo_annotated_image = None
        segmented_img = None
        buffered = None
        buffered_annot = None
        buffered_seg = None
        
        try:
            # Load image from uploaded file or base64 string
            if 'photo' in request.FILES:
                photo_file = request.FILES['photo']
                image = Image.open(photo_file).convert('RGB')
            else:
                data_url = request.POST.get('photo')
                header, encoded = data_url.split(",", 1)
                decoded = base64.b64decode(encoded)
                image = Image.open(io.BytesIO(decoded)).convert('RGB')

            # Run main classifier (skin type + eyes + acne)
            preds = predict(image)
            if "error" in preds:
                return JsonResponse({"error": preds["error"]}, status=400)

            skin_type = preds['type_pred'].lower()
            cropped_face = preds.get("cropped_face")

            buffered = io.BytesIO()
            cropped_face.save(buffered, format="JPEG")
            cropped_face_base64 = base64.b64encode(buffered.getvalue()).decode()
            buffered.close()  # Close BytesIO buffer
            buffered = None

            # Eye colors (top predictions or "Eyes Closed")
            left_eye_color = preds.get("left_eye_color", "Unknown")
            right_eye_color = preds.get("right_eye_color", "Unknown")

            # Title-case eye colors if eyes are not closed
            if isinstance(left_eye_color, str) and "closed" not in left_eye_color.lower():
                left_eye_color = left_eye_color.title()
            if isinstance(right_eye_color, str) and "closed" not in right_eye_color.lower():
                right_eye_color = right_eye_color.title()

            # Acne prediction and confidence
            acne_pred = preds.get("acne_pred", "Unknown")
            acne_confidence = preds.get("acne_confidence", 0)

            # --- Map acne severity codes to labels ---
            acne_mapping = {
                "0": "Clear",
                "1": "Mild",
                "2": "Moderate",
                "3": "Severe",
                "clear": "Clear"
            }
            acne_pred_label = acne_mapping.get(str(acne_pred).lower(), "Unknown")

            # Run YOLOv8 on cropped face to detect detailed skin defects
            yolo_boxes, yolo_annotated_image = detect_skin_defects_yolo(cropped_face)

            buffered_annot = io.BytesIO()
            yolo_annotated_image.save(buffered_annot, format="JPEG")
            yolo_annotated_base64 = base64.b64encode(buffered_annot.getvalue()).decode()
            buffered_annot.close()  # Close BytesIO buffer
            buffered_annot = None
            yolo_annotated_image.close()  # Close PIL image
            yolo_annotated_image = None

            # Run YOLOv8 segmentation model on cropped face
            segmented_img, segmentation_results = segment_skin_conditions(cropped_face)
            
            buffered_seg = io.BytesIO()
            segmented_img.save(buffered_seg, format="JPEG")
            segmented_base64 = base64.b64encode(buffered_seg.getvalue()).decode()
            buffered_seg.close()  # Close BytesIO buffer
            buffered_seg = None
            segmented_img.close()  # Close PIL image
            segmented_img = None

            # ===== Generate Tips (using tips.py) =====
            tips = []

            # Skin type tip
            if skin_type in SKIN_TYPE_TIPS:
                tips.append(SKIN_TYPE_TIPS[skin_type])

            # Eye color tip (one unified tip even if colors differ)
            def _clean_eye(c):
                if not isinstance(c, str):
                    return None
                c2 = c.strip()
                if not c2 or c2.lower() == "unknown" or "closed" in c2.lower():
                    return None
                return c2

            left_clean = _clean_eye(left_eye_color)
            right_clean = _clean_eye(right_eye_color)

            unified_eye = None
            if left_clean and right_clean:
                unified_eye = left_clean if left_clean == right_clean else left_clean  # pick left by default
            else:
                unified_eye = left_clean or right_clean

            if unified_eye in EYE_COLOR_TIPS:
                tips.append(EYE_COLOR_TIPS[unified_eye])

            # Acne tip (use mapped label -> lowercase key for ACNE_TIPS)
            acne_key = acne_pred_label.lower()
            if acne_key in ACNE_TIPS:
                tips.append(ACNE_TIPS[acne_key])

            # Segmentation tips (supports list[str], list[dict], or dict[label->bool])
            seg_labels = []
            if isinstance(segmentation_results, list):
                for it in segmentation_results:
                    if isinstance(it, str):
                        seg_labels.append(it)
                    elif isinstance(it, dict):
                        for k in ("label", "name", "class_name", "class"):
                            v = it.get(k)
                            if isinstance(v, str):
                                seg_labels.append(v)
                                break
            elif isinstance(segmentation_results, dict):
                for k, v in segmentation_results.items():
                    if bool(v):
                        seg_labels.append(k)

            for seg in seg_labels:
                if seg in SEGMENTATION_TIPS:
                    tips.append(SEGMENTATION_TIPS[seg])

            # YOLO tips (supports list[str] or list[dict])
            det_labels = []
            if isinstance(yolo_boxes, list):
                for box in yolo_boxes:
                    if isinstance(box, str):
                        det_labels.append(box)
                    elif isinstance(box, dict):
                        # usual keys: 'label' or 'name'
                        for k in ("label", "name", "class_name", "class"):
                            v = box.get(k)
                            if isinstance(v, str):
                                det_labels.append(v)
                                break

            for lab in det_labels:
                if lab in YOLO_TIPS:
                    tips.append(YOLO_TIPS[lab])

            # De-duplicate tips while preserving order
            seen = set()
            unique_tips = []
            for t in tips:
                if t not in seen:
                    unique_tips.append(t)
                    seen.add(t)
            if not unique_tips:
                unique_tips.append("Your skin looks balanced! Use gentle skincare and enhance naturally with light makeup.")

            # ----- Log FaceAnalysis event -----
            session_key = request.session.session_key
            if not session_key:
                request.session.create()
                session_key = request.session.session_key

            ip = get_client_ip(request)
            device_type = get_device_type(request)

            # Create a FaceAnalysis record to count this analysis event
            FaceAnalysis.objects.create(
                session_key=session_key,
                ip_address=ip,
                device_type=device_type
            )

            # Prepare response data
            response_data = {
                "skin_type": skin_type.title(),
                "acne_pred": acne_pred_label,  # <--- mapped label
                "acne_confidence": round(acne_confidence, 4),
                "cropped_face": f"data:image/jpeg;base64,{cropped_face_base64}",
                "type_probs": preds.get("type_probs", []),
                "yolo_boxes": yolo_boxes,
                "yolo_annotated": f"data:image/jpeg;base64,{yolo_annotated_base64}",
                "left_eye_color": left_eye_color,
                "right_eye_color": right_eye_color,
                "segmentation_overlay": f"data:image/jpeg;base64,{segmented_base64}",
                "segmentation_results": segmentation_results,  # <--- added
                "tips": unique_tips  # <--- added
            }

            if image:
                image.close()
            if cropped_face:
                cropped_face.close()
            
            # Clean up variables
            del image, cropped_face
            if yolo_annotated_image:
                del yolo_annotated_image
            if segmented_img:
                del segmented_img
            gc.collect()

            # ----- Return the analysis results -----
            return JsonResponse(response_data)

        except Exception as e:
            if image:
                image.close()
            if cropped_face:
                cropped_face.close()
            if yolo_annotated_image:
                yolo_annotated_image.close()
            if segmented_img:
                segmented_img.close()
            if buffered:
                buffered.close()
            if buffered_annot:
                buffered_annot.close()
            if buffered_seg:
                buffered_seg.close()
            gc.collect()
            # Return error message with 500 status code on exceptions
            return JsonResponse({"error": str(e)}, status=500)

    # Return error if request method is not POST
    return JsonResponse({"error": "Invalid request method"}, status=400)


# Helper function to get client IP address from request headers
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # Handle cases where multiple IPs exist
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


# Helper function to detect device type from user agent string
def get_device_type(request):
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    if 'mobile' in user_agent:
        return 'Mobile'
    elif 'tablet' in user_agent:
        return 'Tablet'
    return 'Desktop'


# feedback
@csrf_exempt
def submit_feedback(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            feedback_type = data.get("feedback_type")
            dislike_reason = data.get("dislike_reason", "").strip()

            if feedback_type not in ["like", "dislike"]:
                return JsonResponse({"error": "Invalid feedback type"}, status=400)

            if feedback_type == "dislike" and not dislike_reason:
                return JsonResponse({"error": "Dislike reason is required"}, status=400)

            feedback = Feedback(
                feedback_type=feedback_type,
                dislike_reason=dislike_reason if feedback_type == "dislike" else ""
            )
            feedback.save()

            return JsonResponse({"message": "Feedback saved successfully"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid HTTP method"}, status=405)
