import requests
import json

def create_page(shop, token, title="Face Analyzer", body="<h1>Face Analyzer</h1>"):
    """
    Create a page in the Shopify store using GraphQL Admin API.
    Also adds the page to the main menu.
    Returns the page object or None on failure.
    """
    url = f"https://{shop}/admin/api/2025-07/graphql.json"
    headers = {
        "X-Shopify-Access-Token": token,
        "Content-Type": "application/json",
    }

    # --- Step 1: Create the page ---
    query = """
    mutation {
      pageCreate(page: {
        title: "%s",
        body: "%s"
      }) {
        page {
          id
          title
          handle
        }
        userErrors {
          field
          message
        }
      }
    }
    """ % (title, body.replace('"', '\\"'))

    response = requests.post(url, headers=headers, json={"query": query})

    try:
        data = response.json()
    except json.JSONDecodeError:
        print("[ERROR] Response not valid JSON:", response.text)
        return None

    page_data = data.get("data", {}).get("pageCreate", {}).get("page")
    user_errors = data.get("data", {}).get("pageCreate", {}).get("userErrors")

    if not page_data:
        print(f"[WARNING] Failed to create page. Errors: {json.dumps(user_errors, indent=2)}")
        return None

    print(f"[SUCCESS] Page created: {page_data['title']} ({page_data['handle']})")

    # --- Step 2: Fetch main menu ---
    menus_query = """
    {
      menus(first: 10) {
        edges {
          node {
            id
            title
            items {
              id
              title
              type
              url
            }
          }
        }
      }
    }
    """
    menus_resp = requests.post(url, headers=headers, json={"query": menus_query})
    menus_data = menus_resp.json()
    
    main_menu = None
    for edge in menus_data.get("data", {}).get("menus", {}).get("edges", []):
        if edge["node"]["title"].lower() == "main menu":
            main_menu = edge["node"]
            break

    if not main_menu:
        print("[WARNING] Main menu not found. Skipping navigation link creation.")
        return page_data

    # --- Step 3: Prepare menu items for update ---
    menu_items = []
    for item in main_menu["items"]:
        menu_items.append({
            "id": item.get("id"),
            "title": item["title"],
            "type": item["type"],
            "url": item.get("url"),
            "items": []
        })

    # Add new page link
    menu_items.append({
        "id": None,
        "title": page_data["title"],
        "type": "PAGE",
        "url": f"/pages/{page_data['handle']}",
        "resourceId": page_data["id"],
        "items": []
    })

    # --- Step 4: Update menu ---
    update_query = """
    mutation UpdateMenu($id: ID!, $title: String!, $handle: String!, $items: [MenuItemUpdateInput!]!) {
      menuUpdate(id: $id, title: $title, handle: $handle, items: $items) {
        menu {
          id
          handle
          items {
            id
            title
          }
        }
        userErrors {
          field
          message
        }
      }
    }
    """
    variables = {
        "id": main_menu["id"],
        "title": main_menu["title"],
        "handle": main_menu["title"].lower().replace(" ", "-"),
        "items": menu_items
    }
    update_resp = requests.post(url, headers=headers, json={"query": update_query, "variables": variables})
    update_data = update_resp.json()
    if update_data.get("data", {}).get("menuUpdate", {}).get("userErrors"):
        print("[WARNING] Menu update errors:", update_data["data"]["menuUpdate"]["userErrors"])
    else:
        print(f"[SUCCESS] Navigation link added to main menu: {page_data['title']}")

    return page_data
