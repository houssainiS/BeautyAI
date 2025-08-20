from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
from .models import Shop
import json
import urllib.parse
import secrets
import hmac
import hashlib
import requests

from .shopify_api import trigger_install_webhook, register_uninstall_webhook



@csrf_exempt
def install_webhook(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            shop_domain = data.get("myshopify_domain")
            access_token = data.get("access_token")

            if not shop_domain or not access_token:
                return JsonResponse({"error": "Missing shop_domain or access_token"}, status=400)

            shop, created = Shop.objects.update_or_create(
                shop_domain=shop_domain,
                defaults={"access_token": access_token, "active": True}
            )
            return JsonResponse({"message": f"Shop {shop_domain} installed successfully."})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid HTTP method"}, status=405)


def start_oauth(request):
    shop = request.GET.get('shop')  # example: example.myshopify.com
    if not shop:
        return JsonResponse({"error": "Missing shop parameter"}, status=400)

    state = secrets.token_hex(16)
    request.session['oauth_state'] = state

    params = {
        "client_id": settings.SHOPIFY_API_KEY,
        "scope": settings.SHOPIFY_SCOPES,
        "redirect_uri": settings.SHOPIFY_REDIRECT_URI,
        "state": state,
    }

    auth_url = f"https://{shop}/admin/oauth/authorize?" + urllib.parse.urlencode(params)
    return redirect(auth_url)


@csrf_exempt
def oauth_callback(request):
    query_params = request.GET
    shop = query_params.get("shop")
    code = query_params.get("code")
    state = query_params.get("state")
    hmac_param = query_params.get("hmac")

    if state != request.session.get("oauth_state"):
        return JsonResponse({"error": "Invalid state parameter"}, status=400)

    # Verify HMAC
    sorted_params = {k: v for k, v in query_params.items() if k != "hmac"}
    message = "&".join([f"{k}={v}" for k, v in sorted(sorted_params.items())])
    computed_hmac = hmac.new(
        settings.SHOPIFY_API_SECRET.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(computed_hmac, hmac_param):
        return JsonResponse({"error": "HMAC verification failed"}, status=400)

    # Exchange code for access token
    token_url = f"https://{shop}/admin/oauth/access_token"
    response = requests.post(token_url, data={
        "client_id": settings.SHOPIFY_API_KEY,
        "client_secret": settings.SHOPIFY_API_SECRET,
        "code": code
    })
    access_token = response.json().get("access_token")

    if access_token:
        # Save or update the shop
        shop_obj, created = Shop.objects.update_or_create(
            shop_domain=shop,
            defaults={"access_token": access_token, "active": True}
        )

        # Register uninstall webhook automatically
        status, resp = register_uninstall_webhook(shop, access_token)
        print(f"Uninstall webhook status: {status}, response: {resp}")

        # Trigger install webhook automatically
        webhook_status, webhook_resp = trigger_install_webhook(shop, access_token)
        print(f"Install webhook triggered: {webhook_status}, response: {webhook_resp}")

        return JsonResponse({"message": f"Shop {shop} installed successfully!"})
    else:
        return JsonResponse({"error": "Failed to get access token"}, status=400)
