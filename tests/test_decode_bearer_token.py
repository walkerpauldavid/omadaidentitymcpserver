"""
Decode and display bearer token information from bearer.txt

This script reads a bearer token from bearer.txt and decodes it to show:
- Username/subject
- OAuth scope/audience
- Expiry date/time
- Other relevant claims

Usage:
    python test_decode_bearer_token.py
"""

import os
import sys
import json
import base64
from pathlib import Path
from datetime import datetime, timezone

# Add parent directory to path to import from .env
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(parent_dir / '.env')

def read_bearer_token():
    """Read bearer token from bearer.txt in tests folder"""
    token_file = Path(__file__).parent / 'bearer.txt'

    if not token_file.exists():
        print(f"❌ Token file not found: {token_file}")
        print("Please create bearer.txt in the tests folder with your bearer token")
        sys.exit(1)

    with open(token_file, 'r') as f:
        token = f.read().strip()

    # Strip "Bearer " prefix if present
    token = token.replace("Bearer ", "").replace("bearer ", "").strip()

    print(f"✅ Loaded bearer token from {token_file}")
    return token

def decode_jwt_token(token):
    """
    Decode a JWT token without verification.

    JWT tokens have 3 parts separated by dots: header.payload.signature
    We decode the payload (middle part) to read the claims.
    """
    try:
        # Split token into parts
        parts = token.split('.')

        if len(parts) != 3:
            print(f"❌ Invalid JWT token format. Expected 3 parts, got {len(parts)}")
            return None

        header_b64, payload_b64, signature_b64 = parts

        # Decode header
        # Add padding if needed (base64 requires length to be multiple of 4)
        header_b64_padded = header_b64 + '=' * (4 - len(header_b64) % 4)
        header_bytes = base64.urlsafe_b64decode(header_b64_padded)
        header = json.loads(header_bytes)

        # Decode payload
        payload_b64_padded = payload_b64 + '=' * (4 - len(payload_b64) % 4)
        payload_bytes = base64.urlsafe_b64decode(payload_b64_padded)
        payload = json.loads(payload_bytes)

        return {
            'header': header,
            'payload': payload,
            'signature': signature_b64[:20] + '...'  # Just show first 20 chars
        }

    except Exception as e:
        print(f"❌ Error decoding JWT token: {str(e)}")
        print(f"   Exception type: {type(e).__name__}")
        return None

def format_timestamp(timestamp):
    """Convert Unix timestamp to readable datetime string"""
    try:
        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        return dt.strftime('%Y-%m-%d %H:%M:%S UTC')
    except:
        return f"Invalid timestamp: {timestamp}"

def calculate_time_remaining(exp_timestamp):
    """Calculate how much time is left until expiry"""
    try:
        exp_dt = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
        now_dt = datetime.now(tz=timezone.utc)
        remaining = exp_dt - now_dt

        if remaining.total_seconds() < 0:
            return "❌ EXPIRED"

        hours = int(remaining.total_seconds() // 3600)
        minutes = int((remaining.total_seconds() % 3600) // 60)
        seconds = int(remaining.total_seconds() % 60)

        if hours > 0:
            return f"✅ {hours}h {minutes}m {seconds}s remaining"
        elif minutes > 0:
            return f"⚠️  {minutes}m {seconds}s remaining"
        else:
            return f"⚠️  {seconds}s remaining"
    except:
        return "Unknown"

def display_token_info(decoded):
    """Display decoded token information in a human-readable format"""
    if not decoded:
        return

    header = decoded['header']
    payload = decoded['payload']

    print("\n" + "=" * 80)
    print("🔑 TOKEN HEADER")
    print("=" * 80)
    print(f"Algorithm:        {header.get('alg', 'N/A')}")
    print(f"Type:             {header.get('typ', 'N/A')}")
    print(f"Key ID (kid):     {header.get('kid', 'N/A')}")

    print("\n" + "=" * 80)
    print("👤 TOKEN CLAIMS (PAYLOAD)")
    print("=" * 80)

    # User information
    print(f"\n📧 User Information:")
    print(f"   Username (UPN):     {payload.get('upn', 'N/A')}")
    print(f"   Email:              {payload.get('email', payload.get('preferred_username', 'N/A'))}")
    print(f"   Name:               {payload.get('name', 'N/A')}")
    print(f"   Subject (sub):      {payload.get('sub', 'N/A')}")
    print(f"   Object ID (oid):    {payload.get('oid', 'N/A')}")

    # OAuth/Token information
    print(f"\n🔐 OAuth/Token Information:")
    print(f"   Issuer (iss):       {payload.get('iss', 'N/A')}")
    print(f"   Audience (aud):     {payload.get('aud', 'N/A')}")
    print(f"   App ID (appid):     {payload.get('appid', 'N/A')}")
    print(f"   Client ID (azp):    {payload.get('azp', 'N/A')}")

    # Scope information
    scp = payload.get('scp', payload.get('scope', 'N/A'))
    if isinstance(scp, list):
        scp = ' '.join(scp)
    print(f"   Scope (scp):        {scp}")

    # Roles (if any)
    roles = payload.get('roles', [])
    if roles:
        print(f"   Roles:              {', '.join(roles)}")

    # Time information
    print(f"\n⏰ Time Information:")

    iat = payload.get('iat')
    if iat:
        print(f"   Issued At (iat):    {format_timestamp(iat)}")

    nbf = payload.get('nbf')
    if nbf:
        print(f"   Not Before (nbf):   {format_timestamp(nbf)}")

    exp = payload.get('exp')
    if exp:
        print(f"   Expires At (exp):   {format_timestamp(exp)}")
        print(f"   Status:             {calculate_time_remaining(exp)}")

    # Tenant information
    print(f"\n🏢 Tenant Information:")
    print(f"   Tenant ID (tid):    {payload.get('tid', 'N/A')}")
    print(f"   Version (ver):      {payload.get('ver', 'N/A')}")

    # Additional claims
    print(f"\n📋 Additional Claims:")

    # Filter out already displayed claims
    displayed_claims = {
        'upn', 'email', 'preferred_username', 'name', 'sub', 'oid',
        'iss', 'aud', 'appid', 'azp', 'scp', 'scope', 'roles',
        'iat', 'nbf', 'exp', 'tid', 'ver'
    }

    additional_claims = {k: v for k, v in payload.items() if k not in displayed_claims}

    if additional_claims:
        for key, value in sorted(additional_claims.items()):
            # Truncate long values
            if isinstance(value, str) and len(value) > 50:
                value = value[:47] + "..."
            print(f"   {key:20} {value}")
    else:
        print("   (none)")

    print("\n" + "=" * 80)

def main():
    """Main function"""
    print("=" * 80)
    print("🔍 Bearer Token Decoder")
    print("=" * 80)

    # Read bearer token
    token = read_bearer_token()

    print(f"\n📏 Token Length: {len(token)} characters")
    print(f"   Preview: {token[:40]}...{token[-20:]}")

    # Decode token
    print("\n🔓 Decoding JWT token...")
    decoded = decode_jwt_token(token)

    if decoded:
        display_token_info(decoded)
        print("\n✅ Token decoded successfully!")
        return 0
    else:
        print("\n❌ Failed to decode token")
        return 1

if __name__ == "__main__":
    sys.exit(main())
