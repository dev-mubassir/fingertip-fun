import os
import requests
import json

from dotenv import load_dotenv

load_dotenv()

# ==========================================
# 1. SETUP YOUR APP CREDENTIALS
# ==========================================
# All credentials are read from environment variables (loaded from .env).
app_id        = os.environ["INSTAGRAM_APP_ID"]
app_secret    = os.environ["INSTAGRAM_APP_SECRET"]
redirect_uri  = os.environ["REDIRECT_URI"]



# Generate the Instagram OAuth authorization URL
auth_url = (
    f"https://www.instagram.com/oauth/authorize"
    f"?client_id={app_id}"
    f"&redirect_uri={redirect_uri}"
    f"&scope=instagram_business_basic,instagram_business_manage_messages,instagram_business_manage_comments,instagram_business_content_publish"
    f"&response_type=code"
)

print("=" * 50)
print("Open this URL in your browser and authorize the app:")
print("=" * 50)
print(auth_url)
print()
print("After authorization, you will be redirected to a URL like:")
print(f"  {redirect_uri}?code=SOME_CODE#_")
print()
print("Copy the ENTIRE redirect URL from your browser and paste it below:")
print("-" * 50)

returned_url = input("Paste the full redirect URL here: ").strip()

# Extract the authorization code from the returned URL
# Instagram appends "#_" to the redirect URL, so we strip both the redirect_uri prefix and the "#_" suffix
authorization_code = returned_url.replace(redirect_uri + "?code=", "").replace("#_", "").strip()

if not authorization_code:
    print("ERROR: Could not extract a valid authorization code from the URL.")
    print("Make sure the URL contains '?code=' followed by the auth code.")
    exit()

AUTH_CODE = authorization_code
print(f"\nAuthorization code extracted successfully!")
print(f"  Code (first 20 chars): {AUTH_CODE[:20]}...\n")

# ==========================================
# 2. EXCHANGE AUTH CODE FOR SHORT-LIVED TOKEN
# ==========================================
# Instagram Login OAuth requires:
#   - Endpoint: POST https://api.instagram.com/oauth/access_token
#   - Body: form-encoded (not query params)
#   - grant_type: "authorization_code"
print("=" * 50)
print("Fetching Short-Lived Access Token...")
print("=" * 50)

short_token_url = "https://api.instagram.com/oauth/access_token"
short_token_payload = {
    "client_id": app_id,
    "client_secret": app_secret,
    "grant_type": "authorization_code",
    "redirect_uri": redirect_uri,
    "code": AUTH_CODE,
}

# Debug logging (secrets masked)
print(f"  POST {short_token_url}")
print(f"  client_id: {app_id}")
print(f"  client_secret: ***{app_secret[-4:]}")
print(f"  grant_type: authorization_code")
print(f"  redirect_uri: {redirect_uri}")
print(f"  code (first 20 chars): {AUTH_CODE[:20]}...")

response = requests.post(short_token_url, data=short_token_payload)

print(f"  Status Code: {response.status_code}")
print(f"  Response Time: {response.elapsed.total_seconds():.2f}s")
print(f"  Response Body: {response.text}")

short_token_data = response.json()

if "access_token" not in short_token_data:
    print("\nERROR fetching short-lived token:")
    print(json.dumps(short_token_data, indent=4))
    exit()

short_lived_token = short_token_data["access_token"]
user_id = short_token_data.get("user_id", "unknown")
print(f"\nSuccess! Short-Lived Token Retrieved.")
print(f"  User ID: {user_id}")
print(f"  Token (first 20 chars): {short_lived_token[:20]}...\n")

# ==========================================
# 3. EXCHANGE SHORT-LIVED TOKEN FOR LONG-LIVED TOKEN
# ==========================================
# Instagram Login uses:
#   - Endpoint: GET https://graph.instagram.com/access_token
#   - grant_type: "ig_exchange_token" (NOT "fb_exchange_token")
#   - No client_id needed, uses client_secret + access_token
print("=" * 50)
print("Exchanging for Long-Lived Access Token (60 days)...")
print("=" * 50)

long_token_url = "https://graph.instagram.com/access_token"
long_token_payload = {
    "grant_type": "ig_exchange_token",
    "client_secret": app_secret,
    "access_token": short_lived_token,
}

# Debug logging
print(f"  GET {long_token_url}")
print(f"  grant_type: ig_exchange_token")
print(f"  client_secret: ***{app_secret[-4:]}")
print(f"  access_token (first 20 chars): {short_lived_token[:20]}...")

response = requests.get(long_token_url, params=long_token_payload)

print(f"  Status Code: {response.status_code}")
print(f"  Response Time: {response.elapsed.total_seconds():.2f}s")
print(f"  Response Body: {response.text}")

long_token_data = response.json()

if "access_token" not in long_token_data:
    print("\nERROR fetching long-lived token:")
    print(json.dumps(long_token_data, indent=4))
    exit()

long_lived_token = long_token_data["access_token"]
expires_in = long_token_data.get("expires_in", "unknown")
print(f"\nSuccess! Long-Lived Token Retrieved.")
print(f"  Expires in: {expires_in} seconds")
print(f"  Token (first 20 chars): {long_lived_token[:20]}...\n")

# ==========================================
# 4. FETCH DIRECT MESSAGES (DMs)
# ==========================================
# When using Instagram Login tokens (IGAA...), the Conversations API
# must be called on graph.instagram.com (not graph.facebook.com).
# graph.facebook.com cannot parse Instagram Login tokens.
print("=" * 50)
print("Fetching Instagram Conversations & Messages...")
print("=" * 50)
# Use the long-lived token obtained from the current auth session

dm_url = "https://graph.instagram.com/v22.0/me/conversations"

# payload = {
#     "platform": "instagram",
#     "fields": "participants,messages{created_time,from,message,reactions,shares,attachments}",
#     "access_token": long_lived_token,
# }
payload = {
    "platform": "instagram",
    "fields": (
        "id,"
        "updated_time,"
        "participants,"
        "messages.limit(1){"
            "id,"
            "created_time,"
            "from,"
            "message,"
            "attachments,"
            "shares,"
            "reactions,"
            "story,"
            "sticker"
        "}"
    ),
    "limit": 1,  # Latest conversation
    "access_token": long_lived_token,
}

# Debug logging
print(f"  GET {dm_url}")
print(f"  platform: instagram")
print(f"  fields: {payload['fields']}")

dm_response = requests.get(dm_url, params=payload)

print(f"  Status Code: {dm_response.status_code}")
print(f"  Response Time: {dm_response.elapsed.total_seconds():.2f}s")

dm_data = dm_response.json()

# Print the final detailed JSON
print("\nConversations Response:")
print(json.dumps(dm_data, indent=4))