#!/usr/bin/env python3
"""
Threads API 连接测试脚本
验证 config.json 和 API credentials 的有效性
"""

import json
import sys
import os
from datetime import datetime, timedelta

try:
    import requests
except ImportError:
    print("❌ 缺少 requests 库")
    print("   请运行: pip install requests")
    sys.exit(1)

def load_config(config_path="config.json"):
    """加载 config.json"""
    if not os.path.exists(config_path):
        print(f"❌ 找不到 {config_path}")
        return None

    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"❌ {config_path} 格式错误（JSON 解析失败）")
        return None
    except Exception as e:
        print(f"❌ 读取 {config_path} 失败: {e}")
        return None

def check_token_validity(config):
    """检查 Token 有效期"""
    print("\n" + "=" * 70)
    print("📋 Token 有效期检查")
    print("=" * 70)

    platforms = ["instagram", "threads"]
    all_valid = True

    for platform in platforms:
        if platform not in config:
            continue

        data = config[platform]
        expires_at = data.get('expires_at', 0)
        now = int(datetime.now().timestamp())
        remaining_seconds = expires_at - now
        remaining_hours = remaining_seconds / 3600

        print(f"\n🔑 {platform.upper()}")
        print(f"   过期时间: {datetime.fromtimestamp(expires_at).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   当前时间: {datetime.fromtimestamp(now).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   剩余: {remaining_hours:.1f} 小时")

        if remaining_seconds < 0:
            print(f"   ❌ Token 已过期")
            all_valid = False
        elif remaining_seconds < 300:  # 5 分钟
            print(f"   ⚠️  Token 即将过期（< 5 分钟）")
            all_valid = False
        else:
            print(f"   ✅ Token 有效")

    return all_valid

def test_threads_api(config, timeout=10):
    """测试 Threads API 连接"""
    print("\n" + "=" * 70)
    print("🔌 Threads API 连接测试")
    print("=" * 70)

    if "threads" not in config:
        print("❌ config.json 中没有 Threads 配置")
        return False

    threads = config["threads"]
    user_id = threads.get('user_id')
    access_token = threads.get('access_token')

    if not user_id or not access_token:
        print("❌ Threads credentials 不完整")
        return False

    # 检查 token 是否是示例值
    if access_token.startswith("THAAOFOcPsFA1BYlpIUWxIcVM2S3"):
        print(f"\n📱 User ID: {user_id}")
        print(f"🔑 Access Token: {access_token[:30]}...")
        print(f"⏳ 准备发起 API 请求...")

    url = f"https://graph.threads.net/v1.0/{user_id}"
    params = {
        "fields": "id,username,name",
        "access_token": access_token
    }

    try:
        response = requests.get(url, params=params, timeout=timeout)

        print(f"\n📊 响应状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ API 连接成功！")
            print(f"   User ID: {data.get('id')}")
            print(f"   Username: {data.get('username')}")
            print(f"   Name: {data.get('name')}")
            return True

        elif response.status_code == 401:
            error_data = response.json().get('error', {})
            print(f"❌ 认证失败 (401 Unauthorized)")
            print(f"   错误: {error_data.get('message', 'Unknown')}")
            print(f"   💡 解决: 需要刷新 Token (见 references/api-integration.md)")
            return False

        elif response.status_code == 400:
            error_data = response.json().get('error', {})
            print(f"❌ 请求错误 (400 Bad Request)")
            print(f"   错误: {error_data.get('message', str(error_data))}")
            return False

        else:
            print(f"❌ API 错误 ({response.status_code})")
            try:
                error_data = response.json()
                print(f"   错误: {error_data}")
            except:
                print(f"   响应: {response.text[:200]}")
            return False

    except requests.exceptions.Timeout:
        print(f"❌ 请求超时 (timeout)")
        print(f"   💡 检查网络连接或增加超时时间")
        return False

    except requests.exceptions.ConnectionError as e:
        print(f"❌ 连接失败")
        print(f"   错误: {e}")
        return False

    except Exception as e:
        print(f"❌ 未知错误")
        print(f"   错误: {type(e).__name__}: {e}")
        return False

def test_instagram_api(config, timeout=10):
    """测试 Instagram Graph API 连接"""
    print("\n" + "=" * 70)
    print("🔌 Instagram Graph API 连接测试")
    print("=" * 70)

    if "instagram" not in config:
        print("❌ config.json 中没有 Instagram 配置")
        return False

    instagram = config["instagram"]
    user_id = instagram.get('user_id')
    access_token = instagram.get('access_token')

    if not user_id or not access_token:
        print("❌ Instagram credentials 不完整")
        return False

    # 检查是否是示例值
    if access_token == "IGAABXzYourLongLivedAccessTokenHere...":
        print("⚠️  Instagram credentials 仍为示例值")
        print("   需要升级到 Graph API 并获取真实 Token")
        print("   见 references/ig-graph-api-upgrade.md")
        return False

    print(f"\n📱 User ID: {user_id}")
    print(f"🔑 Access Token: {access_token[:20]}...")
    print(f"⏳ 准备发起 API 请求...")

    url = f"https://graph.instagram.com/v24.0/{user_id}"
    params = {
        "fields": "id,username,name",
        "access_token": access_token
    }

    try:
        response = requests.get(url, params=params, timeout=timeout)

        print(f"\n📊 响应状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ API 连接成功！")
            print(f"   User ID: {data.get('id')}")
            print(f"   Username: {data.get('username')}")
            print(f"   Name: {data.get('name')}")
            return True

        else:
            error_data = response.json().get('error', {})
            print(f"❌ API 错误 ({response.status_code})")
            print(f"   错误: {error_data.get('message', str(error_data))}")
            return False

    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def main():
    """主测试流程"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  🧪 OpenClaw Social Post v1.0.0-api API 测试".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝")

    # 加载配置
    config = load_config("config.json")
    if not config:
        print("\n❌ 无法继续测试，请先设置 config.json")
        return False

    print("\n✅ config.json 已加载")

    # 检查 Token 有效期
    tokens_valid = check_token_validity(config)

    # 测试 Threads API
    threads_ok = test_threads_api(config)

    # 测试 Instagram API
    instagram_ok = test_instagram_api(config)

    # 总结
    print("\n" + "=" * 70)
    print("📋 测试总结")
    print("=" * 70)

    print(f"\n🔑 Token 有效期: {'✅' if tokens_valid else '❌'}")
    print(f"🔗 Threads API: {'✅' if threads_ok else '❌'}")
    print(f"📱 Instagram API: {'✅ (可选)' if instagram_ok else '⚠️  需要升级'}")

    if threads_ok:
        print("\n✅ Threads API 连接正常，可以开始测试发文！")
        print("   下一步: 在 OpenClaw 中说「今天发一篇」")
    else:
        print("\n❌ API 连接失败，请检查:")
        print("   1. 网络连接")
        print("   2. Token 有效期")
        print("   3. Credentials 正确性")
        print("   详见 references/api-integration.md")

    print("\n")
    return threads_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
