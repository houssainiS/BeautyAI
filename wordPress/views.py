import uuid
import base64
import io
import gc
import json
from PIL import Image

from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.core.cache import cache 
from .models import WordpressShop, Plan

# --- AI Model Imports (Reused from Recommender App) ---
from recommender.AImodels.ml_model import predict
from recommender.AImodels.yolo_model import detect_skin_defects_yolo
from recommender.AImodels.segment_skin_conditions_yolo import segment_skin_conditions 

def connect_page(request):
    """
    Step 1: Show the user a 'Do you want to connect?' page.
    """
    shop_url = request.GET.get('shop_url')
    admin_email = request.GET.get('admin_email', '')

    if not shop_url:
        return render(request, 'error.html', {'message': 'Missing shop URL'})

    context = {
        'shop_url': shop_url,
        'admin_email': admin_email
    }
    return render(request, 'wordPress/confirm_connect.html', context)

def finalize_connection(request):
    """
    Step 2: User clicked 'Accept'. Create or Update record and redirect back.
    """
    if request.method == "POST":
        shop_url = request.POST.get('shop_url')
        admin_email = request.POST.get('admin_email')

        # Generate a fresh API Key
        new_api_key = uuid.uuid4().hex + uuid.uuid4().hex 
        
        # update_or_create: Finds shop by domain, updates key, or creates new with default plan
        shop, created = WordpressShop.objects.update_or_create(
            domain=shop_url,
            defaults={
                'api_key': new_api_key,     
                'admin_email': admin_email,
                'is_active': True
            }
        )

        cache.delete("allowed_origins") 

        callback_url = f"{shop_url}/wp-admin/admin.php?page=face-analyzer&status=success&api_key={new_api_key}"
        return redirect(callback_url)
    
    return redirect('home')

@csrf_exempt
def deactivate_shop(request):
    """
    Called by WordPress when the 'Disconnect' button is clicked.
    """
    if request.method == "POST":
        shop_url = request.POST.get('shop_url')
        api_key = request.POST.get('api_key')

        shop = WordpressShop.objects.filter(domain=shop_url, api_key=api_key).first()
        if shop:
            shop.is_active = False
            shop.save()
            cache.delete("allowed_origins")
            return JsonResponse({'status': 'success', 'message': 'Shop deactivated'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

@csrf_exempt
def wp_analyze_photo(request):
    """
    Step 3: The actual analysis endpoint for WordPress with Dynamic Quota Check.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    # 1. AUTHENTICATION
    api_key = request.POST.get('api_key')
    shop_url = request.POST.get('shop_url')
    
    if not api_key or not shop_url:
        return JsonResponse({"error": "Missing API Key or Shop URL"}, status=400)

    shop = WordpressShop.objects.filter(domain=shop_url, api_key=api_key, is_active=True).first()
    
    if not shop:
        return JsonResponse({"error": "Unauthorized: Invalid API Key or inactive shop"}, status=401)

    # 2. DYNAMIC QUOTA CHECK
    # This uses the current_limit property from the model based on the Plan
    max_quota = shop.current_limit
    if shop.analysis_this_month >= max_quota:
        return JsonResponse({
            "status": "quota_exceeded",
            "error": "Quota Ended", 
            "message": f"You have reached your limit of {max_quota} analyses. Please upgrade your plan."
        }, status=403)

    # 3. IMAGE PROCESSING & AI ANALYSIS
    image = None
    cropped_face = None
    yolo_annotated_image = None
    segmented_img = None

    try:
        # Load image
        if 'photo' in request.FILES:
            photo_file = request.FILES['photo']
            image = Image.open(photo_file).convert('RGB')
        else:
            data_url = request.POST.get('photo')
            if not data_url:
                return JsonResponse({"error": "No image data provided"}, status=400)
            
            encoded = data_url.split(",", 1)[1] if "," in data_url else data_url
            decoded = base64.b64decode(encoded)
            image = Image.open(io.BytesIO(decoded)).convert('RGB')

        # --- A. Run Main Classifier ---
        preds = predict(image)
        if "error" in preds:
            return JsonResponse({"error": preds["error"]}, status=400)

        skin_type = preds['type_pred'].lower()
        cropped_face = preds.get("cropped_face")

        # Encode Cropped Face
        buffered = io.BytesIO()
        cropped_face.save(buffered, format="JPEG")
        cropped_face_base64 = base64.b64encode(buffered.getvalue()).decode()
        buffered.close()

        # Eye Colors
        left_eye_color = preds.get("left_eye_color", "Unknown")
        right_eye_color = preds.get("right_eye_color", "Unknown")
        if isinstance(left_eye_color, str) and "closed" not in left_eye_color.lower():
            left_eye_color = left_eye_color.title()
        if isinstance(right_eye_color, str) and "closed" not in right_eye_color.lower():
            right_eye_color = right_eye_color.title()

        # Acne Prediction logic
        acne_pred = preds.get("acne_pred", "Unknown")
        acne_confidence = preds.get("acne_confidence", 0)
        acne_mapping = {"0": "Clear", "1": "Mild", "2": "Moderate", "3": "Severe", "clear": "Clear"}
        acne_pred_label = acne_mapping.get(str(acne_pred).lower(), "Unknown")

        # --- B. Run YOLOv8 for Defects ---
        yolo_boxes, yolo_annotated_image = detect_skin_defects_yolo(cropped_face)
        buffered_annot = io.BytesIO()
        yolo_annotated_image.save(buffered_annot, format="JPEG")
        yolo_annotated_base64 = base64.b64encode(buffered_annot.getvalue()).decode()
        buffered_annot.close()

        # --- C. Run YOLOv8 for Segmentation ---
        segmented_img, segmentation_results = segment_skin_conditions(cropped_face)
        buffered_seg = io.BytesIO()
        segmented_img.save(buffered_seg, format="JPEG")
        segmented_base64 = base64.b64encode(buffered_seg.getvalue()).decode()
        buffered_seg.close()

        # 4. UPDATE QUOTA
        shop.analysis_this_month += 1
        shop.analysis_all_time += 1
        shop.save()

        # 5. PREPARE RESPONSE
        response_data = {
            "status": "success",
            "usage": {
                "used": shop.analysis_this_month,
                "limit": max_quota
            },
            "skin_type": skin_type.title(),
            "acne_pred": acne_pred_label,
            "acne_confidence": round(acne_confidence, 4),
            "cropped_face": f"data:image/jpeg;base64,{cropped_face_base64}",
            "type_probs": preds.get("type_probs", []),
            "yolo_boxes": yolo_boxes,
            "yolo_annotated": f"data:image/jpeg;base64,{yolo_annotated_base64}",
            "left_eye_color": left_eye_color,
            "right_eye_color": right_eye_color,
            "segmentation_overlay": f"data:image/jpeg;base64,{segmented_base64}",
            "segmentation_results": segmentation_results
        }

        # Final Memory Cleanup
        if image: image.close()
        if cropped_face: cropped_face.close()
        if yolo_annotated_image: yolo_annotated_image.close()
        if segmented_img: segmented_img.close()
        gc.collect()

        return JsonResponse(response_data)

    except Exception as e:
        if 'image' in locals() and image: image.close()
        if 'cropped_face' in locals() and cropped_face: cropped_face.close()
        gc.collect()
        return JsonResponse({"error": str(e)}, status=500)
    
def wp_shop_status(request):
    api_key = request.GET.get('api_key')
    shop_url = request.GET.get('shop_url')
    
    shop = WordpressShop.objects.filter(domain=shop_url, api_key=api_key, is_active=True).first()
    if not shop:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    return JsonResponse({
        "plan": shop.plan.name,
        "usage": {
            "used": shop.analysis_this_month,
            "limit": shop.current_limit
        }
    })