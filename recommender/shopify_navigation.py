import requests
import json

def create_page(shop, token, title="Face Analyzer", body = """
<style>
  h1.page-title {
    display: none; /* Hide Shopify's default page title */
  }
</style>

<div style="text-align:center; margin-top:50px;">
  <h1 style="font-size: 32px; color: #2c3e50; margin-bottom: 20px;">
     Face Analyzer 
  </h1>
  <p style="font-size: 18px; color: #555;">
    Analyze your face instantly with AI insights
  </p>
</div>
"""
):
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

    # -------------------------
    # STEP 1: Create the page
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

    # -------------------------
    # STEP 2: Fetch all pages
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
    page_map = {node["node"]["title"]: node["node"]["id"] for node in pages_data.get("data", {}).get("pages", {}).get("edges", [])}
    print("Page map:", page_map)

    # -------------------------
    # STEP 3: Fetch main menu
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
        return page_data

    print("Main menu found:", main_menu["id"])

    # -------------------------
    # STEP 4: Build updated menu items
    # -------------------------
    updated_items = []
    for item in main_menu["items"]:
        updated_item = {
            "id": item["id"],
            "title": item["title"],
            "type": item["type"],
            "url": item["url"],
            "items": []
        }
        # Add resourceId for existing PAGE items
        if item["type"] == "PAGE" and item["title"] in page_map:
            updated_item["resourceId"] = page_map[item["title"]]
        updated_items.append(updated_item)

    # Add new page
    if title in page_map:
        updated_items.append({
            "id": None,
            "title": title,
            "type": "PAGE",
            "url": f"/pages/{page_map[title].split('/')[-1]}",
            "resourceId": page_map[title],
            "items": []
        })

    print("Valid menu items for update:")
    for it in updated_items:
        print(it)

    # -------------------------
    # STEP 5: Update menu
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

    return page_data
