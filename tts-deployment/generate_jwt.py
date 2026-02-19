import jwt
import sys
from datetime import datetime, timedelta

# JWT secret from argument or generate new one
secret = "/HWoqwJ4l1nakz9BP52KFXccpzy61dh5qvkjLtxHno4="

# Generate anon key (public)
anon_payload = {
    "iss": "supabase",
    "ref": "local",
    "role": "anon",
    "iat": int(datetime.utcnow().timestamp()),
    "exp": int((datetime.utcnow() + timedelta(days=3650)).timestamp())  # 10 years
}
anon_key = jwt.encode(anon_payload, secret, algorithm="HS256")

# Generate service_role key (private)
service_payload = {
    "iss": "supabase",
    "ref": "local",
    "role": "service_role",
    "iat": int(datetime.utcnow().timestamp()),
    "exp": int((datetime.utcnow() + timedelta(days=3650)).timestamp())  # 10 years
}
service_key = jwt.encode(service_payload, secret, algorithm="HS256")

print(f"ANON_KEY={anon_key}")
print(f"SERVICE_KEY={service_key}")
