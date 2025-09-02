# webhooks.py
import requests
import hmac, hashlib, base64
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Shop

SHOPIFY_API_SECRET = "your_api_secret"


def verify_webhook(data, hmac_header):
    digest = hmac.new(
        SHOPIFY_API_SECRET.encode("utf-8"),
        data,
        hashlib.sha256
    ).digest()
    calculated_hmac = base64.b64encode(digest).decode()
    return hmac.compare_digest(calculated_hmac, hmac_header)


@csrf_exempt
def app_uninstalled(request):
    hmac_header = request.headers.get("X-Shopify-Hmac-Sha256")

    if not verify_webhook(request.body, hmac_header):
        return JsonResponse({"error": "Invalid webhook"}, status=401)

    shop = request.headers.get("X-Shopify-Shop-Domain")
    if shop:
        Shop.objects.filter(domain=shop).delete()
        print(f"App uninstalled from {shop}")

    return JsonResponse({"status": "ok"})


def register_uninstall_webhook(shop, access_token):
    url = f"https://{shop}/admin/api/2023-10/webhooks.json"
    headers = {
        "X-Shopify-Access-Token": access_token,
        "Content-Type": "application/json"
    }
    data = {
        "webhook": {
            "topic": "app/uninstalled",
            "address": "https://your-backend.com/webhooks/app_uninstalled/",
            "format": "json"
        }
    }
    response = requests.post(url, json=data, headers=headers)
    print("Webhook response:", response.json())
