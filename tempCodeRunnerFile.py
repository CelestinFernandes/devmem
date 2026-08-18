import socket
import requests

# Manually resolve the domain using Google DNS
def resolve_host(host):
    try:
        # Use socket to resolve (this uses system DNS)
        ip = socket.gethostbyname(host)
        print(f"Resolved {host} -> {ip}")
        return ip
    except Exception as e:
        print(f"Failed to resolve: {e}")
        return None

# Try to resolve
host = "api-inference.huggingface.co"
ip = resolve_host(host)

if ip:
    # Test the connection
    try:
        response = requests.get(f"https://{ip}/status", headers={"Host": host}, timeout=10)
        print(f"✅ Connection successful! Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
else:
    print("❌ Could not resolve host.")