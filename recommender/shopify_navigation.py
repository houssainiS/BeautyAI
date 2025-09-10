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

    # GraphQL mutation exactly like the working curl command
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

    if page_data:
        print(f"[SUCCESS] Page created: {page_data['title']} ({page_data['handle']})")
        return page_data
    else:
        print(f"[WARNING] Failed to create page. Errors: {json.dumps(user_errors, indent=2)}")
        return None
