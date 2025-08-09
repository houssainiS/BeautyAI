from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from PIL import Image
import base64
import io
import json

from recommender.AImodels.ml_model import predict
from recommender.AImodels.yolo_model import detect_skin_defects_yolo
from recommender.AImodels.segment_skin_conditions_yolo import segment_skin_conditions  # <-- Added

from .models import FaceAnalysis , Feedback # Import your FaceAnalysis model


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

            # Convert cropped face to base64 for JSON response
            buffered = io.BytesIO()
            cropped_face.save(buffered, format="JPEG")
            cropped_face_base64 = base64.b64encode(buffered.getvalue()).decode()

            # Eye colors (top predictions or "Eyes Closed")
            left_eye_color = preds.get("left_eye_color", "Unknown")
            right_eye_color = preds.get("right_eye_color", "Unknown")

            # Title-case eye colors if eyes are not closed
            if "closed" not in left_eye_color.lower():
                left_eye_color = left_eye_color.title()
            if "closed" not in right_eye_color.lower():
                right_eye_color = right_eye_color.title()

            # Acne prediction and confidence
            acne_pred = preds.get("acne_pred", "Unknown")
            acne_confidence = preds.get("acne_confidence", 0)

            # Run YOLOv8 on cropped face to detect detailed skin defects
            yolo_boxes, yolo_annotated_image = detect_skin_defects_yolo(cropped_face)

            # Convert YOLO annotated image to base64
            buffered_annot = io.BytesIO()
            yolo_annotated_image.save(buffered_annot, format="JPEG")
            yolo_annotated_base64 = base64.b64encode(buffered_annot.getvalue()).decode()

            # Run YOLOv8 segmentation model on cropped face
            segmented_img, _ = segment_skin_conditions(cropped_face)
            buffered_seg = io.BytesIO()
            segmented_img.save(buffered_seg, format="JPEG")
            segmented_base64 = base64.b64encode(buffered_seg.getvalue()).decode()

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

            # ----- Return the analysis results -----
            return JsonResponse({
                "skin_type": skin_type.title(),
                "acne_pred": acne_pred,
                "acne_confidence": round(acne_confidence, 4),
                "cropped_face": f"data:image/jpeg;base64,{cropped_face_base64}",
                "type_probs": preds.get("type_probs", []),
                "yolo_boxes": yolo_boxes,
                "yolo_annotated": f"data:image/jpeg;base64,{yolo_annotated_base64}",
                "left_eye_color": left_eye_color,
                "right_eye_color": right_eye_color,
                "segmentation_overlay": f"data:image/jpeg;base64,{segmented_base64}"
            })

        except Exception as e:
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


#feedback
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