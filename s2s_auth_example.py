import jwt
import requests
import hashlib
import time

host = "PBX_name.wildixin.com"
appKey = "s2s-8381s2s-###################"
appSecret = "##########################################"
appName = "8381s2s"
path = '/api/v1/PBX/settings/CallQueues/'

canonicalRequest = 'GET/api/v1/PBX/settings/CallQueues/host:PBX_name.wildixin.com;x-app-id:s2s-8381s2s-###################;'

timestamp = int(time.time())
expire = timestamp + 24 * 60 * 60  # 24 hours in seconds

payload = {
    'iss': appName,
    'iat': timestamp,
    'exp': timestamp + expire,
    'sign': {
        'alg': 'sha256',
        'headers': ['Host', 'X-APP-ID'],
        'hash': hashlib.sha256(canonicalRequest.encode()).hexdigest()
    }
}

token = jwt.encode(payload, appSecret, algorithm='HS256')
print(token)

url = f"https://{host}{path}"
headers = {
    "Host": host,
    "X-APP-ID": appKey,
    "Authorization": f"Bearer {token}"
}

try:
    r = requests.get(url, headers=headers)
    print(r.json())
    r.raise_for_status()  # raises an exception for non-2XX responses
    print(f"API GET request sent to {url}")
    print(r)
except requests.exceptions.RequestException as e:
    print(f"Error sending API GET request to {url}: {e}")