import requests
import json

def trigger_install_webhook(shop_domain, access_token):
    url = "http://127.0.0.1:8000/shopify/webhook/install/"
    payload = {
        "myshopify_domain": shop_domain,
        "access_token": access_token
    }
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        return response.status_code, response.json()
    except Exception as e:
        return None, {"error": str(e)}

def register_uninstall_webhook(shop_domain, access_token):
    url = f"https://{shop_domain}/admin/api/2023-10/webhooks.json"
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": access_token
    }
    payload = {
        "webhook": {
            "topic": "app/uninstalled",
            "address": "http://127.0.0.1:8000/shopify/webhook/install/",
            "format": "json"
        }
    }

    response = requests.post(url, json=payload, headers=headers)
    return response.status_code, response.json()
