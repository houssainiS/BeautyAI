import requests
import json

def create_page(shop, token, title="Face Analyzer", body="<h1>Face Analyzer</h1>"):
    """
    Create a page in the Shopify store using GraphQL Admin API.
    Returns the page object or None on failure.
    """
    url = f"https://{shop}/admin/api/2025-07/graphql.json"
    headers = {
        "X-Shopify-Access-Token": token,
        "Content-Type": "application/json",
    }
    query = """
    mutation {
      pageCreate(page: {title: "%s", body: "%s"}) {
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
    data = response.json()
    
    if response.status_code == 200 and data.get("data", {}).get("pageCreate", {}).get("page"):
        return data["data"]["pageCreate"]["page"]
    else:
        print(f"[WARNING] Failed to create page: {json.dumps(data, indent=2)}")
        return None


def add_link_to_main_menu(shop, token, page_id, link_title="Face Analyzer"):
    """
    Add a link to the main navigation menu pointing to the page using GraphQL.
    """
    url = f"https://{shop}/admin/api/2025-07/graphql.json"
    headers = {
        "X-Shopify-Access-Token": token,
        "Content-Type": "application/json",
    }

    # GraphQL mutation to create a menu item
    query = """
    mutation {
      menuItemCreate(menuItem: {
        title: "%s",
        type: PAGE,
        pageId: "%s",
        menuId: "gid://shopify/Menu/1"
      }) {
        menuItem {
          id
          title
        }
        userErrors {
          field
          message
        }
      }
    }
    """ % (link_title, page_id)

    response = requests.post(url, headers=headers, json={"query": query})
    data = response.json()

    if response.status_code == 200 and data.get("data", {}).get("menuItemCreate", {}).get("menuItem"):
        return data["data"]["menuItemCreate"]["menuItem"]
    else:
        print(f"[WARNING] Failed to add menu item: {json.dumps(data, indent=2)}")
        return None
