import requests
import socket

url = "https://abmuzxugpqzbrwfewhri.supabase.co"
key = "sb_publishable_7Z-G7bZAgJiA4780C3TlhA_YDxO8IU7"

print(f"Testing connection to: {url}")
print(f"API Key: {key}")
print("=" * 50)

# Test DNS resolution
try:
    host = url.replace("https://", "").replace("http://", "").split("/")[0]
    print(f"Resolving host: {host}")
    ip = socket.gethostbyname(host)
    print(f"DNS Resolution successful: {ip}")
except socket.gaierror as e:
    print(f"DNS Resolution failed: {e}")
    print("\nPossible causes:")
    print("1. The Supabase project doesn't exist")
    print("2. The project is paused")
    print("3. The URL is incorrect")
    print("4. Network/firewall issue")
    exit(1)

# Test HTTP connection
try:
    headers = {
        'apikey': key,
        'Authorization': f'Bearer {key}',
    }
    response = requests.get(f"{url}/rest/v1/", headers=headers, timeout=10)
    print(f"\nHTTP Status Code: {response.status_code}")
    print(f"Response: {response.text[:200]}")
except requests.exceptions.RequestException as e:
    print(f"HTTP Connection failed: {e}")
