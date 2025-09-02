# shopify_api.py
import requests

def create_expiration_metafield(shop, access_token):
    url = f"https://{shop}/admin/api/2023-10/metafield_definitions.json"
    headers = {
        "X-Shopify-Access-Token": access_token,
        "Content-Type": "application/json"
    }
    data = {
        "metafield_definition": {
            "name": "Expiration Date",
            "namespace": "custom",
            "key": "expiration_date",
            "type": "date",
            "owner_type": "Product"
        }
    }
    response = requests.post(url, json=data, headers=headers)
    print("Metafield response:", response.json())
