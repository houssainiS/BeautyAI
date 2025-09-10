import requests

def create_page(shop, token, title="Face Analyzer", body_html="<h1>Face Analyzer</h1>"):
    """
    Create a page in the Shopify store using REST Admin API.
    Returns the page object or None on failure.
    """
    url = f"https://{shop}/admin/api/2025-07/pages.json"
    headers = {
        "X-Shopify-Access-Token": token,
        "Content-Type": "application/json",
    }
    payload = {
        "page": {
            "title": title,
            "body_html": body_html,
            "published": True
        }
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 201:
        return response.json().get("page")
    else:
        print(f"[WARNING] Failed to create page: {response.text}")
        return None


def add_link_to_main_menu(shop, token, page_id, link_title="Face Analyzer"):
    """
    Add a link to the main navigation menu pointing to the page.
    """
    # Step 1: Get the main menu
    menu_url = f"https://{shop}/admin/api/2025-07/menus.json"
    headers = {"X-Shopify-Access-Token": token}
    menus_response = requests.get(menu_url, headers=headers)
    if menus_response.status_code != 200:
        print(f"[WARNING] Failed to fetch menus: {menus_response.text}")
        return None

    menus = menus_response.json().get("menus", [])
    main_menu = next((m for m in menus if m.get("handle") == "main-menu"), None)
    if not main_menu:
        print("[WARNING] Main menu not found")
        return None

    # Step 2: Add the link
    menu_item_url = f"https://{shop}/admin/api/2025-07/menus/{main_menu['id']}/menu_items.json"
    payload = {
        "menu_item": {
            "title": link_title,
            "type": "page_link",
            "page_id": page_id
        }
    }
    resp = requests.post(menu_item_url, json=payload, headers=headers)
    if resp.status_code == 201:
        return resp.json().get("menu_item")
    else:
        print(f"[WARNING] Failed to add menu item: {resp.text}")
        return None
