#!/usr/bin/env python3
"""Test conversations/channels endpoint"""
import requests
import json
import sys
import os

BASE_URL = os.getenv("BRIDGECORE_TEST_BASE_URL", "https://bridgecore.geniura.com")
TEST_EMAIL = os.getenv("BRIDGECORE_TEST_EMAIL")
TEST_PASSWORD = os.getenv("BRIDGECORE_TEST_PASSWORD")

def test_login():
    """Test login to get token"""
    if not TEST_EMAIL or not TEST_PASSWORD:
        print("❌ Missing BRIDGECORE_TEST_EMAIL or BRIDGECORE_TEST_PASSWORD")
        return None

    url = f"{BASE_URL}/api/v1/auth/tenant/login"
    data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    print(f"🔐 Attempting login with {data['email']}...")
    response = requests.post(url, json=data)
    
    if response.status_code == 200:
        token_data = response.json()
        token = token_data.get("access_token")
        print(f"✅ Login successful!")
        print(f"   Token: {token[:50]}...")
        return token
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return None

def test_conversations_channels(token):
    """Test conversations/channels endpoint"""
    url = f"{BASE_URL}/api/v1/conversations/channels"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print(f"\n📡 Testing GET {url}...")
    response = requests.get(url, headers=headers)
    
    print(f"   Status Code: {response.status_code}")
    print(f"   Response Headers: {dict(response.headers)}")
    
    try:
        response_data = response.json()
        print(f"   Response Body:")
        print(json.dumps(response_data, indent=2))
    except:
        print(f"   Response Text: {response.text}")
    
    return response.status_code == 200

if __name__ == "__main__":
    print("="*60)
    print("Testing Conversations Channels Endpoint")
    print("="*60)
    
    # Try to login
    token = test_login()
    
    if not token:
        print("\n⚠️  Cannot test endpoint without valid token")
        print("   Trying with invalid token to see error handling...")
        test_conversations_channels("invalid_token")
        sys.exit(1)
    
    # Test endpoint
    success = test_conversations_channels(token)
    
    if success:
        print("\n✅ Test passed!")
    else:
        print("\n❌ Test failed!")
        sys.exit(1)










