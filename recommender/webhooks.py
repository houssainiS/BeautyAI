# webhooks.py
import requests
import hmac, hashlib, base64
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Shop

# Replace this with your real Shopify API secret from your app settings
SHOPIFY_API_SECRET = "bea4550804b2d95776ecc77dd992fd3f"


def verify_webhook(data, hmac_header):
    """
    Verifies Shopify webhook HMAC
    """
    digest = hmac.new(
        SHOPIFY_API_SECRET.encode("utf-8"),
        data,
        hashlib.sha256
    ).digest()
    calculated_hmac = base64.b64encode(digest).decode()
    return hmac.compare_digest(calculated_hmac, hmac_header)


@csrf_exempt
def app_uninstalled(request):
    """
    Handles app/uninstalled webhook from Shopify
    Deletes the shop from the database
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    hmac_header = request.headers.get("X-Shopify-Hmac-Sha256")
    if not hmac_header or not verify_webhook(request.body, hmac_header):
        return JsonResponse({"error": "Invalid webhook"}, status=401)

    shop_domain = request.headers.get("X-Shopify-Shop-Domain")
    if shop_domain:
        Shop.objects.filter(domain=shop_domain).delete()
        print(f"App uninstalled from {shop_domain}")

    # MUST return 200 OK to Shopify
    return JsonResponse({"status": "ok"}, status=200)


def register_uninstall_webhook(shop, access_token):
    """
    Registers the app/uninstalled webhook for a specific shop
    Call this when a merchant installs the app
    """
    url = f"https://{shop}/admin/api/2023-10/webhooks.json"
    headers = {
        "X-Shopify-Access-Token": access_token,
        "Content-Type": "application/json"
    }
    data = {
        "webhook": {
            "topic": "app/uninstalled",
            "address": "https://beautyai.duckdns.org/webhooks/app_uninstalled/",
            "format": "json"
        }
    }
    response = requests.post(url, json=data, headers=headers)
    print("Webhook registration response:", response.json())
