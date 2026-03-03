from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.http import JsonResponse
from django.db.models import F, Q, Count
from PIL import Image
import base64
import io
import json
import gc  # garbage collection import
from datetime import datetime, timedelta
from django.utils import timezone

from recommender.AImodels.ml_model import predict
from recommender.AImodels.yolo_model import detect_skin_defects_yolo
from recommender.AImodels.segment_skin_conditions_yolo import segment_skin_conditions  

from .models import FaceAnalysis, Feedback , Visitor

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

                # ✅ Validate file size (max 10 MB)
                max_size = 10 * 1024 * 1024  # 10 MB
                if photo_file.size > max_size:
                    return JsonResponse({"error": "File too large (max 10 MB allowed)."}, status=400)

                # ✅ Validate file extension
                valid_extensions = ['jpg', 'jpeg', 'png']
                extension = photo_file.name.split('.')[-1].lower()
                if extension not in valid_extensions:
                    return JsonResponse({"error": "Invalid file type. Only PNG, JPG, and JPEG are allowed."}, status=400)

                image = Image.open(photo_file).convert('RGB')
            else:
                data_url = request.POST.get('photo')
                header, encoded = data_url.split(",", 1)
                decoded = base64.b64decode(encoded)

                # ✅ Validate base64 image size (max 10 MB)
                if len(decoded) > 10 * 1024 * 1024:
                    return JsonResponse({"error": "Image too large (max 10 MB allowed)."}, status=400)

                image = Image.open(io.BytesIO(decoded)).convert('RGB')

                # ✅ Validate image format
                if image.format not in ["JPEG", "JPG", "PNG"]:
                    return JsonResponse({"error": "Unsupported image format."}, status=400)

            # Run main classifier (skin type + eyes + acne)
            preds = predict(image)
            if "error" in preds:
                return JsonResponse({"error": preds["error"]}, status=400)

            skin_type = preds['type_pred'].lower()
            cropped_face = preds.get("cropped_face")

            buffered = io.BytesIO()
            cropped_face.save(buffered, format="JPEG")
            cropped_face_base64 = base64.b64encode(buffered.getvalue()).decode()
            buffered.close()
            buffered = None

            # Eye colors (top predictions or "Eyes Closed")
            left_eye_color = preds.get("left_eye_color", "Unknown")
            right_eye_color = preds.get("right_eye_color", "Unknown")

            if isinstance(left_eye_color, str) and "closed" not in left_eye_color.lower():
                left_eye_color = left_eye_color.title()
            if isinstance(right_eye_color, str) and "closed" not in right_eye_color.lower():
                right_eye_color = right_eye_color.title()

            # Acne prediction and confidence
            acne_pred = preds.get("acne_pred", "Unknown")
            acne_confidence = preds.get("acne_confidence", 0)

            acne_mapping = {
                "0": "Clear",
                "1": "Mild",
                "2": "Moderate",
                "3": "Severe",
                "clear": "Clear"
            }
            acne_pred_label = acne_mapping.get(str(acne_pred).lower(), "Unknown")

            # Run YOLOv8 on cropped face
            yolo_boxes, yolo_annotated_image = detect_skin_defects_yolo(cropped_face)

            buffered_annot = io.BytesIO()
            yolo_annotated_image.save(buffered_annot, format="JPEG")
            yolo_annotated_base64 = base64.b64encode(buffered_annot.getvalue()).decode()
            buffered_annot.close()
            buffered_annot = None
            yolo_annotated_image.close()
            yolo_annotated_image = None

            # Run YOLOv8 segmentation
            segmented_img, segmentation_results = segment_skin_conditions(cropped_face)
            
            buffered_seg = io.BytesIO()
            segmented_img.save(buffered_seg, format="JPEG")
            segmented_base64 = base64.b64encode(buffered_seg.getvalue()).decode()
            buffered_seg.close()
            buffered_seg = None
            segmented_img.close()
            segmented_img = None

            # ----- Log FaceAnalysis event -----
            session_key = request.session.session_key
            if not session_key:
                request.session.create()
                session_key = request.session.session_key

            ip = get_client_ip(request)
            device_type = get_device_type(request)
            domain = get_domain(request)

            FaceAnalysis.objects.create(
                session_key=session_key,
                ip_address=ip,
                device_type=device_type,
                domain=domain
            )

            # ----- Face analysis Increment Shop Counter -----
            if domain:
                # 1. Clean the domain string
                clean_domain = domain.replace("https://", "").replace("http://", "").strip("/")
                
                # 2. Find the shop (Optimized query using Q for "either/or")
                shop_obj = Shop.objects.filter(Q(domain=clean_domain) | Q(custom_domain=clean_domain)).first()

                # 3. Atomic Increment
                if shop_obj:
                    try:
                        shop_obj.analysis_count = F("analysis_count") + 1
                        shop_obj.save(update_fields=["analysis_count"])
                    except Exception as db_err:
                        print(f"Non-critical error incrementing counter: {db_err}")
            # ---------------------------------------------

            # Response data (NO backend tips anymore)
            response_data = {
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

            if image:
                image.close()
            if cropped_face:
                cropped_face.close()
            
            del image, cropped_face
            if yolo_annotated_image:
                del yolo_annotated_image
            if segmented_img:
                del segmented_img
            gc.collect()

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
            return JsonResponse({"error": str(e)}, status=500)

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

# Helper function to get Shopify domain from request
def get_domain(request):
    return request.POST.get("shop", "") or request.META.get("HTTP_ORIGIN", "")

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


##############webhooks############
import os
import requests
from django.shortcuts import redirect, render
from django.conf import settings
import urllib.parse
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt

from .models import Shop, PageContent
from .webhooks import register_uninstall_webhook, register_gdpr_webhooks , register_shop_update_webhook
from .shopify_navigation import create_page  # only import the working function

# Load from environment variables with fallback
SHOPIFY_API_KEY = os.getenv("SHOPIFY_API_KEY", "fallback-key-for-dev")
SHOPIFY_API_SECRET = os.getenv("SHOPIFY_API_SECRET", "fallback-secret-for-dev")


def app_entry(request):
    shop = request.GET.get("shop")
    if not shop:
        return render(request, "error.html", {"message": "Missing shop parameter"})

    page_created = request.GET.get("page_created") == "1"

    # 1. Try to find the shop
    shop_obj = Shop.objects.filter(domain=shop).first()

    # 2. Check if the shop is "Ready": Exists + Active + Has Token
    # This logic "repairs" shops that were added manually but have no token
    if shop_obj and shop_obj.is_active and shop_obj.offline_token:
        # Shop is fully set up, show the dashboard
        context = {
            "shop": shop,
            "theme_editor_link": shop_obj.theme_editor_link,
            "page_created": page_created,
            "api_key": SHOPIFY_API_KEY,
            "analysis_count": shop_obj.analysis_count,
        }
        return render(request, "recommender/shopify_install_page.html", context)
    
    else:
        # If shop doesn't exist OR is missing a token OR is inactive:
        # Start Auth to "Repair" or "Install" the shop automatically.
        return redirect(f"/start_auth/?shop={shop}")


def oauth_callback(request):
    """
    Handles Shopify OAuth callback.
    Saves/reactivates the shop, FETCHES CUSTOM DOMAIN, EMAIL, and registers webhooks.
    """
    try:
        shop = request.GET.get("shop")
        code = request.GET.get("code")

        if not shop or not code:
            return JsonResponse({"error": "Missing shop or code"}, status=400)

        # Exchange code for access token
        response = requests.post(
            f"https://{shop}/admin/oauth/access_token",
            data={
                "client_id": SHOPIFY_API_KEY,
                "client_secret": SHOPIFY_API_SECRET,
                "code": code,
            },
        )
        data = response.json()
        offline_token = data.get("access_token")
        online_token = data.get("online_access_info", {}).get("access_token")

        if not offline_token:
            return JsonResponse({"error": "OAuth failed", "details": data}, status=400)

        # --- NEW LOGIC START: Fetch Shop Details ---
        shop_details_url = f"https://{shop}/admin/api/2024-01/shop.json"
        headers = {"X-Shopify-Access-Token": offline_token}
        detail_response = requests.get(shop_details_url, headers=headers)
        
        primary_custom_domain = None
        actual_shop_name = None
        shop_email = None  # Initialize variable

        if detail_response.status_code == 200:
            shop_data = detail_response.json().get('shop', {})
            
            # Extract data
            primary_custom_domain = shop_data.get('domain') 
            actual_shop_name = shop_data.get('name')
            shop_email = shop_data.get('email') 
        # --- NEW LOGIC END ---

        # Save/reactivate shop with NEW fields
        shop_obj, created = Shop.objects.update_or_create(
            domain=shop,
            defaults={
                "offline_token": offline_token,
                "online_token": online_token,
                "custom_domain": primary_custom_domain,
                "shop_name": actual_shop_name,
                "email": shop_email,  
                "is_active": True,
            },
        )

        # Register Webhooks
        register_uninstall_webhook(shop, offline_token)
        register_gdpr_webhooks(shop, offline_token)
        register_shop_update_webhook(shop, offline_token)

        return render(
            request,
            "recommender/shopify_install_page.html",
            {"shop": shop, "theme_editor_link": shop_obj.theme_editor_link},
        )

    except Exception as e:
        print(f"[ERROR] Exception in oauth_callback: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({"error": f"Server error: {e}"}, status=500)


def create_shopify_page(request):
    """
    Creates the Face Analyzer page and navigation link manually
    when merchant clicks the button.
    """
    shop = request.GET.get("shop")
    if not shop:
        return render(request, "error.html", {"message": "Missing shop parameter"})

    try:
        shop_obj = Shop.objects.get(domain=shop, is_active=True)
        page_content = PageContent.objects.first()
        if not page_content:
            page_content = PageContent(title="Face Analyzer", body="<h1>Face Analyzer</h1>")

        page, deep_link = create_page(
            shop,
            shop_obj.offline_token,
            title=page_content.title,
            body=page_content.body,
            api_key=SHOPIFY_API_KEY,
            block_type="Beautyxia",
        )

        if page:
            shop_obj.theme_editor_link = deep_link
            shop_obj.save()
            messages.success(request, "✅ Page created and added to menu successfully.")
        else:
            messages.error(request, "⚠️ Failed to create page or add to menu.")

        return redirect(f"/app_entry/?shop={shop}&page_created=1")

    except Shop.DoesNotExist:
        return redirect(f"/start_auth/?shop={shop}")

def start_auth(request):
    """
    Starts the Shopify OAuth installation flow.
    Redirects merchant to Shopify to approve the app.
    """
    try:
        shop = request.GET.get("shop")
        if not shop:
            return render(request, "error.html", {"message": "Missing shop parameter"})

        redirect_uri = settings.BASE_URL + "/auth/callback/"
        scopes = (
            "write_online_store_pages,read_online_store_pages,read_online_store_navigation,"
            "write_online_store_navigation,read_themes"
        )

        auth_url = (
            f"https://{shop}/admin/oauth/authorize?"
            f"client_id={SHOPIFY_API_KEY}&"
            f"scope={scopes}&"
            f"redirect_uri={urllib.parse.quote(redirect_uri)}&"
            f"state=12345"
        )

        return redirect(auth_url)

    except Exception as e:
        print(f"[ERROR] Exception in start_auth: {e}")
        return render(request, "error.html", {"message": f"Server error: {e}"})


### docs & policies

def documentation(request):
    """
    Render the documentation.
    """
    return render(request, "recommender/documentation.html")


def privacy_policy(request):
    """
    Render the privacy_policy.
    """
    return render(request, "recommender/privacy-policy.html")



############# dashboard #############


@login_required
def dashboard(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('staff_login')
        
    # Use timezone.now() instead of now()
    today_dt = timezone.now()
    today = today_dt.date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    # 1. Top Card Stats
    stats = {
        "total_visitors": Visitor.objects.count(),
        "analysis_today": FaceAnalysis.objects.filter(timestamp__date=today).count(),
        "analysis_week": FaceAnalysis.objects.filter(timestamp__date__gte=week_ago).count(),
        "analysis_month": FaceAnalysis.objects.filter(timestamp__date__gte=month_ago).count(),
        "likes": Feedback.objects.filter(feedback_type="like").count(),
        "dislikes": Feedback.objects.filter(feedback_type="dislike").count(),
    }

    # 2. Trends Logic
    visitor_trend_labels, visitor_trend_data = [], []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        visitor_trend_labels.append(date.strftime("%b %d"))
        visitor_trend_data.append(Visitor.objects.filter(date=date).count())

    analysis_today_labels, analysis_today_counts = [], []
    # FIX: Create a timezone-aware midnight for today
    midnight = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.min.time()))
    
    for hour in range(24):
        hour_start = midnight + timedelta(hours=hour)
        hour_end = hour_start + timedelta(hours=1)
        analysis_today_labels.append(f"{hour:02d}:00")
        # Comparison is now Aware vs Aware
        analysis_today_counts.append(
            FaceAnalysis.objects.filter(timestamp__gte=hour_start, timestamp__lt=hour_end).count()
        )

    analysis_week_labels, analysis_week_data = [], []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        analysis_week_labels.append(date.strftime("%b %d"))
        analysis_week_data.append(FaceAnalysis.objects.filter(timestamp__date=date).count())

    analysis_month_labels, analysis_month_data = [], []
    for i in range(29, -1, -1):
        date = today - timedelta(days=i)
        label = date.strftime("%b %d") if i % 3 == 0 or i == 0 else ""
        analysis_month_labels.append(label)
        analysis_month_data.append(FaceAnalysis.objects.filter(timestamp__date=date).count())

    # 3. Tables Data
    analysis_logs = FaceAnalysis.objects.filter(timestamp__date__gte=month_ago).order_by('-timestamp')
    shops = Shop.objects.filter(is_active=True).order_by("-analysis_count")

    # 4. Device Split
    device_stats = FaceAnalysis.objects.filter(timestamp__date__gte=month_ago).values('device_type').annotate(count=Count('id'))
    device_labels = [d['device_type'] if d['device_type'] else 'Desktop' for d in device_stats]
    device_counts = [d['count'] for d in device_stats]

    context = {
        "stats": stats,
        "visitor_trend_labels": json.dumps(visitor_trend_labels),
        "visitor_trend_data": json.dumps(visitor_trend_data),
        "analysis_today_labels": json.dumps(analysis_today_labels),
        "analysis_today_data": json.dumps(analysis_today_counts),
        "analysis_week_labels": json.dumps(analysis_week_labels),
        "analysis_week_data": json.dumps(analysis_week_data),
        "analysis_month_labels": json.dumps(analysis_month_labels),
        "analysis_month_data": json.dumps(analysis_month_data),
        "feedback_data": json.dumps([stats["likes"], stats["dislikes"]]),
        "device_labels": json.dumps(device_labels),
        "device_counts": json.dumps(device_counts),
        "analysis_logs": analysis_logs,
        "domain_stats": shops,
    }
    return render(request, "recommender/dashboard.html", context)


@login_required
def search_domains(request):
    query = request.GET.get('domain', '')
    sort_by = request.GET.get('sort', 'analyses')
    shops = Shop.objects.filter(is_active=True)
    
    if query:
        shops = shops.filter(Q(domain__icontains=query) | Q(custom_domain__icontains=query) | Q(shop_name__icontains=query))
    
    if sort_by == 'newest':
        shops = shops.order_by('-created_at')
    else:
        shops = shops.order_by('-analysis_count')

    results = []
    for s in shops:
        results.append({
            "title": s.shop_name or "No Title",
            "domain": s.custom_domain or s.domain,
            "installed_on": s.created_at.strftime("%b %d, %Y"),
            "analysis_count": s.analysis_count
        })
    return JsonResponse({"domains": results})


@login_required
def filter_logs(request):
    device = request.GET.get('device', '')
    # Use timezone.now()
    month_ago = timezone.now().date() - timedelta(days=30)
    logs = FaceAnalysis.objects.filter(timestamp__date__gte=month_ago).order_by('-timestamp')
    if device:
        logs = logs.filter(device_type__iexact=device)
    
    results = [{"time": l.timestamp.strftime("%b %d, %H:%M"), "domain": l.domain or "Unknown", "device": l.device_type or "Desktop", "ip": l.ip_address or "0.0.0.0"} for l in logs]
    return JsonResponse({"logs": results})


def staff_login(request):
    # Already logged in? Send to dashboard
    if request.user.is_authenticated:
        return redirect('dashboard')

    error = None

    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_staff or user.is_superuser:
                login(request, user)
                return redirect('dashboard')
            else:
                error = "You are not authorized to access the staff dashboard."
        else:
            error = "Invalid username or password."

    return render(request, 'recommender/login.html', {'error': error})


def staff_logout(request):
    logout(request)
    return redirect('staff_login')
