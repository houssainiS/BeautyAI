import requests

def create_expiration_metafield(shop, access_token):
    url = f"https://{shop}/admin/api/2025-07/metafields.json"
    headers = {
        "X-Shopify-Access-Token": access_token,
        "Content-Type": "application/json"
    }
    data = {
        "metafield": {
            "namespace": "subscription",
            "key": "expiration_date",
            "value": "2025-12-31",
            "type": "single_line_text_field"
        }
    }
    response = requests.post(url, json=data, headers=headers)
    
    # Safely print the response
    try:
        print("Metafield response:", response.json())
    except ValueError:
        print("Metafield response is not JSON:", response.text)
