#!/usr/bin/env python3
"""
Threads API Token Refresh Script
刷新 config.json 中的 Access Token
"""

import json
import requests
import time
from datetime import datetime

def refresh_threads_token(config_path="config.json"):
    """
    刷新 Threads Access Token

    使用长期有效的 Refresh Token 来获取新的 Access Token
    """

    print("=" * 70)
    print("Threads Token Refresh Script")
    print("=" * 70)

    # 1. 读取配置
    print("\n[1] Reading config.json...")
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except Exception as e:
        print("[ERROR] Cannot read config.json: " + str(e))
        return False

    threads = config.get('threads', {})
    app_id = threads.get('app_id')
    app_secret = threads.get('app_secret')
    access_token = threads.get('access_token')
    user_id = threads.get('user_id')

    print("[OK] Config loaded")
    print("     User ID: " + user_id)
    print("     App ID: " + app_id)

    # 2. 检查 Token 过期状态
    print("\n[2] Checking token expiry...")
    expires_at = threads.get('expires_at', 0)
    now = int(time.time())

    if expires_at > now:
        remaining_hours = (expires_at - now) / 3600
        print("[OK] Token still valid for {:.1f} hours".format(remaining_hours))
        print("     Expiry: " + datetime.fromtimestamp(expires_at).strftime('%Y-%m-%d %H:%M:%S'))
        return True
    else:
        print("[WARN] Token expired")
        print("     Expired: " + datetime.fromtimestamp(expires_at).strftime('%Y-%m-%d %H:%M:%S'))

    # 3. Refresh Token
    print("\n[3] Attempting to refresh token...")
    print("     Using refresh endpoint...")

    # Threads uses Instagram refresh token endpoint
    url = "https://graph.instagram.com/refresh_access_token"
    params = {
        'grant_type': 'ig_refresh_token',
        'access_token': access_token
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        print("     Response: " + str(response.status_code))

        if response.status_code == 200:
            data = response.json()
            new_token = data.get('access_token')
            new_expires = data.get('expires_in', 5184000)  # Default 60 days

            # Update config
            new_expires_at = int(time.time()) + new_expires
            config['threads']['access_token'] = new_token
            config['threads']['expires_at'] = new_expires_at

            # Also update Instagram if exists
            if 'instagram' in config:
                config['instagram']['access_token'] = new_token
                config['instagram']['expires_at'] = new_expires_at

            # Save config
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)

            print("[SUCCESS] Token refreshed!")
            print("     New token valid for {:.0f} days".format(new_expires / 86400))
            print("     New expiry: " + datetime.fromtimestamp(new_expires_at).strftime('%Y-%m-%d %H:%M:%S'))
            print("     Config saved to: " + config_path)

            return True
        else:
            error = response.json()
            error_msg = error.get('error', {}).get('message', str(error))
            print("[ERROR] Token refresh failed: " + error_msg)
            return False

    except Exception as e:
        print("[ERROR] Request failed: " + str(e))
        return False

if __name__ == "__main__":
    import sys
    success = refresh_threads_token("config.json")
    sys.exit(0 if success else 1)
