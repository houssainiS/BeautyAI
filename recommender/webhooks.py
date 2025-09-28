# webhooks.py
import requests
import hmac
import hashlib
import base64
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import Shop, Purchase
import os

SHOPIFY_API_SECRET = os.getenv("SHOPIFY_API_SECRET", "fallback-secret-for-dev")


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


@csrf_exempt
def app_uninstalled(request):
    """
    Handles Shopify 'app/uninstalled' webhook.
    Marks the shop as inactive and deletes its saved metafield definition.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    hmac_header = request.headers.get("X-Shopify-Hmac-Sha256")
    if not hmac_header:
        print("[Webhook] Missing HMAC header")
        return JsonResponse({"error": "Missing HMAC header"}, status=400)

    if not verify_webhook(request.body, hmac_header):
        print("[Webhook] HMAC verification failed")
        return JsonResponse({"error": "Invalid webhook"}, status=401)

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

        # --- Step 3: Mark shop inactive ---
        shop_obj.is_active = False
        shop_obj.save(update_fields=["is_active"])
        print(f"[Webhook] App uninstalled from {shop_domain}, marked inactive")

    except Exception as e:
        print(f"[Webhook] Exception handling uninstall for {shop_domain}: {e}")

    return JsonResponse({"status": "ok"}, status=200)


def register_uninstall_webhook(shop, access_token):
    """
    Registers the 'app/uninstalled' webhook for a specific shop.
    Call this function when a merchant installs the app.
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

    try:
        response = requests.post(url, json=data, headers=headers)
        print("[Webhook Registration] Response:", response.json())
    except Exception as e:
        print("[Webhook Registration] Failed to register webhook:", str(e))
        print("[Webhook Registration] Raw response text:", getattr(response, "text", "No response text"))


# ==========================================================
# 📌 Orders/Updated Webhook Registration & Endpoint
# ==========================================================
from django.conf import settings
from django.utils import timezone

# -------------------------------
# Fetch usage duration metafield
# -------------------------------

def fetch_usage_duration(product_id, shop_domain):
    """
    Fetch usage_duration metafield for a product via GraphQL.
    """
    try:
        shop = Shop.objects.get(domain=shop_domain)
        graphql_url = f"https://{shop_domain}/admin/api/2025-07/graphql.json"
        headers = {
            "X-Shopify-Access-Token": shop.offline_token,
            "Content-Type": "application/json",
        }
        query = """
        query($id: ID!) {
          product(id: $id) {
            metafield(namespace: "custom", key: "usage_duration") {
              value
            }
          }
        }
        """
        variables = {"id": f"gid://shopify/Product/{product_id}"}
        resp = requests.post(
            graphql_url,
            headers=headers,
            json={"query": query, "variables": variables}
        )
        value = resp.json().get("data", {}).get("product", {}).get("metafield", {}).get("value")
        return int(value) if value else 0
    except Exception as e:
        print(f"[Webhook] Failed to fetch usage_duration: {e}")
        return 0


# -------------------------------
# Register orders/updated webhook
# -------------------------------

def register_orders_updated_webhook(shop_domain, access_token):
    """
    Registers the 'orders/updated' webhook for a shop with detailed debugging.
    """
    url = f"https://{shop_domain}/admin/api/2025-07/webhooks.json"
    headers = {
        "X-Shopify-Access-Token": access_token,
        "Content-Type": "application/json"
    }
    data = {
        "webhook": {
            "topic": "orders/updated",  # ✅ supported topic
            "address": f"{settings.BASE_URL}/webhooks/order_updated/",
            "format": "json"
        }
    }

    try:
        response = requests.post(url, json=data, headers=headers)

        # Print status code
        print("[Webhook Registration] HTTP Status Code:", response.status_code)

        # Try parsing JSON safely
        try:
            resp_json = response.json()
            print("[Webhook Registration] Response JSON:", resp_json)
            if "errors" in resp_json:
                print("[Webhook Registration] Shopify returned errors:", resp_json["errors"])
            elif "webhook" in resp_json:
                print("[Webhook Registration] Webhook successfully registered:", resp_json["webhook"])
            else:
                print("[Webhook Registration] Unexpected response format")
        except ValueError as json_err:
            print("[Webhook Registration] Failed to parse JSON:", json_err)
            print("[Webhook Registration] Raw response text:", response.text)

    except requests.RequestException as req_err:
        print("[Webhook Registration] Request failed:", req_err)


# -------------------------------
# Handle order_updated webhook
# -------------------------------

@csrf_exempt
def order_updated(request):
    """
    Endpoint to receive Shopify 'orders/updated' webhook.
    Only saves purchase when financial_status == 'paid'.
    Includes detailed debugging.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    # --- DEBUG: Log all headers ---
    print("[Webhook Debug] Headers:", dict(request.headers))

    # --- DEBUG: Log raw body safely ---
    try:
        body_text = request.body.decode()
        print("[Webhook Debug] Raw body:", body_text)
    except Exception as decode_err:
        print("[Webhook Debug] Failed to decode body:", decode_err)
        body_text = ""

    # --- Verify HMAC ---
    hmac_header = request.headers.get("X-Shopify-Hmac-Sha256")
    if not hmac_header or not verify_webhook(request.body, hmac_header):
        print("[Webhook Debug] Invalid HMAC or missing header")
        return JsonResponse({"error": "Invalid webhook"}, status=401)

    try:
        # Parse JSON
        data = {}
        if body_text:
            try:
                data = json.loads(body_text)
            except json.JSONDecodeError as json_err:
                print("[Webhook Debug] Failed to parse JSON:", json_err)

        # Get shop
        shop_domain = request.headers.get("X-Shopify-Shop-Domain")
        shop = Shop.objects.filter(domain=shop_domain).first()
        if not shop:
            print(f"[Webhook Debug] Shop not found: {shop_domain}")
            return JsonResponse({"error": "Shop not found"}, status=404)

        # Check financial_status
        financial_status = data.get("financial_status")
        if financial_status != "paid":
            print(f"[Webhook Debug] Order ignored, financial_status={financial_status}")
            return JsonResponse({"status": "ignored"}, status=200)

        # Extract order info
        email = data.get("email")
        phone = data.get("phone")
        order_id = data.get("id")
        line_items = data.get("line_items", [])

        print(f"[Webhook] Paid order {order_id} from email={email}, phone={phone} in {shop_domain}")

        for item in line_items:
            product_id = item.get("product_id")
            product_name = item.get("title")
            usage_days = fetch_usage_duration(product_id, shop_domain)

            Purchase.objects.create(
                email=email,
                phone=phone,
                order_id=str(order_id),
                product_id=str(product_id),
                product_name=product_name,
                purchase_date=timezone.now(),
                usage_duration_days=usage_days,
            )
            print(f"[Webhook] Saved purchase: {product_name} ({usage_days} days) for email={email}, phone={phone}")

    except Exception as e:
        print("[Orders/Updated Webhook] Exception:", e)
        import traceback
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"status": "ok"}, status=200)
