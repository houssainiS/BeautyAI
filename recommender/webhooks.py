import requests
import hmac
import hashlib
import base64
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Shop
import os

# ======================================================
# LOAD SHOPIFY API SECRET
# ======================================================
SHOPIFY_API_SECRET = os.getenv("SHOPIFY_API_SECRET", "fallback-secret-for-dev")


# ======================================================
# HMAC VERIFICATION FUNCTION
# ======================================================
def verify_webhook(data, hmac_header):
    """
    Verifies Shopify webhook HMAC to ensure request authenticity.
    """
    digest = hmac.new(
        SHOPIFY_API_SECRET.encode("utf-8"),
        data,
        hashlib.sha256
    ).digest()
    calculated_hmac = base64.b64encode(digest).decode()
    return hmac.compare_digest(calculated_hmac, hmac_header)


# ======================================================
# APP UNINSTALLED WEBHOOK
# ======================================================
@csrf_exempt
def app_uninstalled(request):
    """
    Handles Shopify 'app/uninstalled' webhook.
    Marks the shop as inactive and deletes its saved metafield definition.
    Also removes any stored theme editor deep link.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    # --- Verify webhook authenticity ---
    hmac_header = request.headers.get("X-Shopify-Hmac-Sha256")
    if not hmac_header:
        print("[Webhook] Missing HMAC header")
        return JsonResponse({"error": "Missing HMAC header"}, status=400)

    if not verify_webhook(request.body, hmac_header):
        print("[Webhook] HMAC verification failed")
        return JsonResponse({"error": "Invalid webhook"}, status=401)

    # --- Get shop domain ---
    shop_domain = request.headers.get("X-Shopify-Shop-Domain")
    if not shop_domain:
        return JsonResponse({"error": "Missing shop domain"}, status=400)

    try:
        shop_obj = Shop.objects.filter(domain=shop_domain).first()
        if not shop_obj:
            print(f"[Webhook] No shop record found for {shop_domain}")
            return JsonResponse({"status": "ok"}, status=200)

        # Shopify GraphQL endpoint
        graphql_url = f"https://{shop_domain}/admin/api/2025-07/graphql.json"
        headers = {
            "X-Shopify-Access-Token": shop_obj.offline_token,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # --- Step 1: Get metafield definition ID if not saved ---
        def_id = shop_obj.metafield_definition_id
        if not def_id:
            query = """
            {
              metafieldDefinitions(first: 10, ownerType: PRODUCT, namespace: "custom", key: "usage_duration") {
                edges { node { id } }
              }
            }
            """
            resp = requests.post(graphql_url, headers=headers, json={"query": query})
            edges = resp.json().get("data", {}).get("metafieldDefinitions", {}).get("edges", [])
            if edges:
                def_id = edges[0]["node"]["id"]
                print(f"[Webhook] Found definition ID via query: {def_id}")

        # --- Step 2: Delete metafield definition if found ---
        if def_id:
            delete_query = """
            mutation metafieldDefinitionDelete($id: ID!) {
              metafieldDefinitionDelete(id: $id) {
                deletedDefinitionId
                userErrors { field message }
              }
            }
            """
            variables = {"id": def_id}
            try:
                del_resp = requests.post(graphql_url, headers=headers, json={"query": delete_query, "variables": variables})
                print("[Webhook] Metafield definition delete response:", del_resp.json())
            except Exception as del_e:
                print("[Webhook] Failed to delete metafield definition:", del_e)
        else:
            print("[Webhook] No metafield definition to delete.")

        # --- Step 3: Mark shop inactive & clear theme editor link ---
        shop_obj.is_active = False
        shop_obj.theme_editor_link = None
        shop_obj.save(update_fields=["is_active", "theme_editor_link"])
        print(f"[Webhook] App uninstalled from {shop_domain}, marked inactive and cleared theme_editor_link")

    except Exception as e:
        print(f"[Webhook] Exception handling uninstall for {shop_domain}: {e}")

    return JsonResponse({"status": "ok"}, status=200)


# ======================================================
# REGISTER UNINSTALL WEBHOOK
# ======================================================
def register_uninstall_webhook(shop, access_token):
    """
    Registers the 'app/uninstalled' webhook for a specific shop.
    Call this function when a merchant installs the app.
    """
    url = f"https://{shop}/admin/api/2025-07/webhooks.json"
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

    try:
        response = requests.post(url, json=data, headers=headers)
        print("[Webhook Registration] Response:", response.json())
    except Exception as e:
        print("[Webhook Registration] Failed to register webhook:", str(e))
        print("[Webhook Registration] Raw response text:", getattr(response, "text", "No response text"))


# ======================================================
# GDPR MANDATORY WEBHOOKS (Required for App Approval)
# ======================================================

@csrf_exempt
def customers_data_request(request):
    """
    Handles 'customers/data_request' webhook.
    Shopify sends this when a customer requests to view their stored data.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    # Verify HMAC
    hmac_header = request.headers.get("X-Shopify-Hmac-Sha256")
    if not verify_webhook(request.body, hmac_header):
        print("[GDPR] Invalid HMAC for customers/data_request")
        return JsonResponse({"error": "Invalid webhook"}, status=401)

    data = json.loads(request.body.decode("utf-8"))
    print("[GDPR] Customer data request received:", data)

    # ✅ You don't store customer data, just acknowledge the request
    print("[GDPR] No customer data stored in app.")
    return JsonResponse({"status": "ok"}, status=200)


@csrf_exempt
def customers_redact(request):
    """
    Handles 'customers/redact' webhook.
    Shopify sends this when a customer requests their personal data be deleted.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    # Verify HMAC
    hmac_header = request.headers.get("X-Shopify-Hmac-Sha256")
    if not verify_webhook(request.body, hmac_header):
        print("[GDPR] Invalid HMAC for customers/redact")
        return JsonResponse({"error": "Invalid webhook"}, status=401)

    data = json.loads(request.body.decode("utf-8"))
    print("[GDPR] Customer redact request received:", data)

    # ✅ You don't store customer data, just acknowledge
    print("[GDPR] No customer data stored in app to delete.")
    return JsonResponse({"status": "ok"}, status=200)


@csrf_exempt
def shop_redact(request):
    """
    Handles 'shop/redact' webhook.
    Shopify sends this when a store owner requests deletion after uninstall.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    # Verify HMAC
    hmac_header = request.headers.get("X-Shopify-Hmac-Sha256")
    if not verify_webhook(request.body, hmac_header):
        print("[GDPR] Invalid HMAC for shop/redact")
        return JsonResponse({"error": "Invalid webhook"}, status=401)

    data = json.loads(request.body.decode("utf-8"))
    shop_domain = data.get("shop_domain")
    print(f"[GDPR] Shop redact request received for: {shop_domain}")

    # ✅ Keep shop data for your records — don’t delete it
    print(f"[GDPR] Shop data retained for compliance/logging (not deleted).")
    return JsonResponse({"status": "ok"}, status=200)


# ======================================================
# REGISTER GDPR WEBHOOKS (Automatically after Install)
# ======================================================
def register_gdpr_webhooks(shop, access_token):
    """
    Registers all mandatory GDPR webhooks after app installation.
    Shopify requires these 3:
      - customers/data_request
      - customers/redact
      - shop/redact
    """
    topics = {
        "customers/data_request": "https://beautyai.duckdns.org/webhooks/customers_data_request/",
        "customers/redact": "https://beautyai.duckdns.org/webhooks/customers_redact/",
        "shop/redact": "https://beautyai.duckdns.org/webhooks/shop_redact/",
    }

    for topic, address in topics.items():
        url = f"https://{shop}/admin/api/2025-07/webhooks.json"
        headers = {
            "X-Shopify-Access-Token": access_token,
            "Content-Type": "application/json"
        }
        data = {
            "webhook": {
                "topic": topic,
                "address": address,
                "format": "json"
            }
        }

        try:
            response = requests.post(url, json=data, headers=headers)
            print(f"[GDPR Webhook Registration] {topic}: {response.json()}")
        except Exception as e:
            print(f"[GDPR Webhook Registration] Failed for {topic}:", str(e))
