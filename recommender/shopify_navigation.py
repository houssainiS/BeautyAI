import requests
import json

def get_published_theme_id(shop, token):
    """
    Fetch the main published theme ID for the shop.
    """
    url = f"https://{shop}/admin/api/2025-07/graphql.json"
    headers = {"X-Shopify-Access-Token": token, "Content-Type": "application/json"}
    query = """
    {
      themes(first:10) {
        edges {
          node {
            id
            role
          }
        }
      }
    }
    """
    resp = requests.post(url, headers=headers, json={"query": query})
    data = resp.json()
    for edge in data.get("data", {}).get("themes", {}).get("edges", []):
        if edge["node"]["role"].lower() == "main":
            return edge["node"]["id"].split("/")[-1]  # numeric ID
    return None

def build_theme_editor_link(shop, api_key, block_type, theme_id, page_handle):
    """
    Build a Shopify Theme Editor deep link with Add App Block popup.
    """
    store_handle = shop.split(".myshopify.com")[0]  # Strip domain suffix
    return (
        f"https://admin.shopify.com/store/{store_handle}/themes/{theme_id}/editor"
        f"?addAppBlockId={api_key}/{block_type}"
        f"&footer=true"
        f"&previewPath=/pages/{page_handle}"
    )

def create_page(shop, token, title="Face Analyzer", body="<h1>Face Analyzer</h1>", api_key=None, block_type="test"):
    """
    Create a page in the Shopify store using GraphQL Admin API.
    Also adds the page to the main menu and returns the page object.
    Additionally returns the Theme Editor deep link for adding the app block.
    Returns: (page_data, deep_link) or (None, None) on failure
    """
    url = f"https://{shop}/admin/api/2025-07/graphql.json"
    headers = {"X-Shopify-Access-Token": token, "Content-Type": "application/json"}

    # -------------------------
    # STEP 0: Fetch all pages to check for existing
    # -------------------------
    query_pages = """
    {
      pages(first: 50) {
        edges {
          node {
            id
            title
            handle
          }
        }
      }
    }
    """
    response_pages = requests.post(url, headers=headers, json={"query": query_pages})
    pages_data = response_pages.json()
    page_map = {node["node"]["title"].lower(): node["node"] for node in pages_data.get("data", {}).get("pages", {}).get("edges", [])}

    if title.lower() in page_map:
        page_data = page_map[title.lower()]
        print(f"✅ Page already exists: {page_data['title']} (/{page_data['handle']})")
    else:
        # -------------------------
        # STEP 1: Create page
        # -------------------------
        query_create_page = """
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

        response = requests.post(url, headers=headers, json={"query": query_create_page})
        data = response.json()
        page_data = data.get("data", {}).get("pageCreate", {}).get("page")
        user_errors = data.get("data", {}).get("pageCreate", {}).get("userErrors")
        if not page_data:
            print(f"[WARNING] Failed to create page. Errors: {json.dumps(user_errors, indent=2)}")
            return None, None
        print(f"[SUCCESS] Page created: {page_data['title']} ({page_data['handle']})")

    # Refresh page map after creation
    response_pages = requests.post(url, headers=headers, json={"query": query_pages})
    pages_data = response_pages.json()
    page_map = {node["node"]["title"]: node["node"]["id"] for node in pages_data.get("data", {}).get("pages", {}).get("edges", [])}

    # -------------------------
    # STEP 2: Fetch main menu
    # -------------------------
    query_menus = """
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
              items {
                id
                title
              }
            }
          }
        }
      }
    }
    """
    response_menus = requests.post(url, headers=headers, json={"query": query_menus})
    menus_data = response_menus.json()

    main_menu = None
    for edge in menus_data.get("data", {}).get("menus", {}).get("edges", []):
        if edge["node"]["title"] == "Main menu":
            main_menu = edge["node"]
            break

    if not main_menu:
        print("[WARNING] Main menu not found. Skipping navigation link creation.")
    else:
        print("Main menu found:", main_menu["id"])

        # -------------------------
        # STEP 3: Build updated menu items with duplication check 
        # -------------------------
        updated_items = []
        existing_titles = set()
        for item in main_menu["items"]:
            updated_item = {
                "id": item["id"],
                "title": item["title"],
                "type": item["type"],
                "url": item["url"],
                "items": []
            }
            if item["type"] == "PAGE" and item["title"] in page_map:
                updated_item["resourceId"] = page_map[item["title"]]
            updated_items.append(updated_item)
            existing_titles.add(item["title"])

        # Only add the page if it's not already in the menu
        if title not in existing_titles and title in page_map:
            updated_items.append({
                "id": None,
                "title": title,
                "type": "PAGE",
                "url": f"/pages/{page_data['handle']}",
                "resourceId": page_map[title],
                "items": []
            })

        print("Valid menu items for update:")
        for it in updated_items:
            print(it)

        # -------------------------
        # STEP 4: Update menu
        # -------------------------
        mutation_update_menu = """
        mutation UpdateMenu($id: ID!, $title: String!, $handle: String!, $items: [MenuItemUpdateInput!]!) {
          menuUpdate(id: $id, title: $title, handle: $handle, items: $items) {
            menu {
              id
              handle
              items {
                id
                title
                items {
                  id
                  title
                }
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
            "handle": "main-menu",
            "items": updated_items
        }

        update_resp = requests.post(url, headers=headers, json={"query": mutation_update_menu, "variables": variables})
        update_data = update_resp.json()
        if update_data.get("data", {}).get("menuUpdate", {}).get("userErrors"):
            print("[WARNING] Menu update errors:", update_data["data"]["menuUpdate"]["userErrors"])
        else:
            print(f"[SUCCESS] Navigation link added to main menu: {page_data['title']}")

    # -------------------------
    # STEP 5: Build Theme Editor deep link
    # -------------------------
    theme_id = get_published_theme_id(shop, token)
    deep_link = None
    if theme_id and api_key:
        deep_link = build_theme_editor_link(shop, api_key, block_type, theme_id, page_data['handle'])
        print(f"[SUCCESS] Theme Editor deep link: {deep_link}")

    return page_data, deep_link
