#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Instagram Graph API Diagnostic Script
Tests token validity, permissions, and account setup WITHOUT posting anything.

Usage:
    python test_instagram.py
    python test_instagram.py --config /path/to/config.json
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime

import requests


# -- Helpers ------------------------------------------------------------------

def ok(msg):  print(f"  [OK]   {msg}")
def warn(msg): print(f"  [WARN] {msg}")
def fail(msg): print(f"  [FAIL] {msg}")
def info(msg): print(f"  [INFO] {msg}")


def load_config(config_path: str) -> dict:
    try:
        with open(config_path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[ERROR] Config not found: {config_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON in config: {e}")
        sys.exit(1)


# -- Tests ---------------------------------------------------------------------

def test_config(ig: dict) -> bool:
    """Check config.json Instagram section completeness."""
    print("\n[1/5] Config check")
    print("      -" * 20)

    required = ["user_id", "access_token", "app_id"]
    missing = [k for k in required if not ig.get(k)]

    if missing:
        fail(f"Missing fields in config.json: {missing}")
        info("Run: python -c \"from post_to_social import update_instagram_in_config; "
             "update_instagram_in_config(user_id='...', access_token='...')\"")
        return False

    # Placeholder detection
    placeholders = ["YOUR_", "YourLong", "abc123", "example"]
    uid = ig.get("user_id", "")
    tok = ig.get("access_token", "")

    if any(p in uid for p in placeholders):
        fail("user_id is still a placeholder. Set your real Instagram Business User ID.")
        return False
    if any(p in tok for p in placeholders):
        fail("access_token is still a placeholder. Obtain Instagram User Access Token.")
        info("See references/instagram.md section 'Take Instagram User Access Token'")
        return False

    ok(f"user_id: {uid}")
    ok(f"app_id:  {ig.get('app_id')}")
    ok(f"access_token: {tok[:20]}...{tok[-6:]}")

    # Token expiry
    expires_at = ig.get("expires_at", 0)
    if expires_at > 0:
        remaining = (expires_at - time.time()) / 86400
        if remaining < 0:
            fail(f"Token EXPIRED {abs(remaining):.0f} days ago. Refresh immediately.")
            info("Run: python -c \"from post_to_social import refresh_instagram_token; refresh_instagram_token()\"")
            return False
        elif remaining < 7:
            warn(f"Token expires in {remaining:.0f} days. Refresh soon.")
        else:
            ok(f"Token valid for {remaining:.0f} days (expires {datetime.fromtimestamp(expires_at).strftime('%Y-%m-%d')})")
    else:
        warn("expires_at not set. Run a token refresh to set expiry.")

    ok(f"api_version: {ig.get('api_version', 'v21.0 (default)')}")
    ok(f"host: {ig.get('host', 'graph.instagram.com (default)')}")
    return True


def test_token_validity(ig: dict) -> bool:
    """
    Test token validity via /me endpoint.
    GET https://graph.instagram.com/me?fields=id,username,account_type
    """
    print("\n[2/5] Token validity check -- GET /me")
    print("      -" * 20)

    token = ig["access_token"]
    api_version = ig.get("api_version", "v24.0")
    host = ig.get("host", "graph.instagram.com")
    url = f"https://{host}/{api_version}/me"

    params = {
        "fields": "id,username,account_type,followers_count",
        "access_token": token,
    }

    try:
        resp = requests.get(url, params=params, timeout=15)
        data = resp.json()

        if resp.status_code == 200:
            returned_id = data.get("id")
            config_id = ig.get("user_id")
            username = data.get("username", "N/A")
            account_type = data.get("account_type", "N/A")
            followers = data.get("followers_count", "N/A")

            ok(f"Token valid!")
            ok(f"username:     @{username}")
            ok(f"account_type: {account_type}")
            ok(f"user_id:      {returned_id}")
            if followers != "N/A":
                ok(f"followers:    {followers:,}")

            if returned_id != config_id:
                warn(f"user_id mismatch: config={config_id}, token={returned_id}")
                warn("Update config.json with the correct user_id.")

            if account_type not in ("BUSINESS", "MEDIA_CREATOR"):
                warn(f"account_type is '{account_type}'. Must be BUSINESS or MEDIA_CREATOR to publish.")
                info("Go to Instagram App -> Settings -> Account -> Switch to Professional Account")
                return False
            return True

        else:
            err = data.get("error", {})
            code = err.get("code")
            msg = err.get("message", "Unknown error")
            fail(f"HTTP {resp.status_code} -- Code {code}: {msg}")

            if code == 190:
                info("Token is invalid or expired. Get a new token.")
                info("See references/instagram.md for token setup.")
            elif code == 100:
                info("Invalid parameter. Check user_id and api_version in config.json.")

            return False

    except requests.RequestException as exc:
        fail(f"Request failed: {exc}")
        return False


def test_permissions(ig: dict) -> bool:
    """
    Check granted permissions on the token.
    GET /{user_id}/permissions
    """
    print("\n[3/5] Permission check -- GET /{user_id}/permissions")
    print("      -" * 20)

    token = ig["access_token"]
    user_id = ig["user_id"]
    api_version = ig.get("api_version", "v24.0")
    host = ig.get("host", "graph.instagram.com")
    url = f"https://{host}/{api_version}/{user_id}/permissions"

    required_perms = {"instagram_business_basic", "instagram_business_content_publish"}

    try:
        resp = requests.get(url, params={"access_token": token}, timeout=15)
        data = resp.json()

        if resp.status_code == 200:
            granted = {
                p["permission"]
                for p in data.get("data", [])
                if p.get("status") == "granted"
            }
            declined = {
                p["permission"]
                for p in data.get("data", [])
                if p.get("status") == "declined"
            }

            ok(f"Granted permissions: {sorted(granted)}")

            missing = required_perms - granted
            if missing:
                fail(f"Missing required permissions: {missing}")
                info("Re-authorize via Meta OAuth with the correct scopes:")
                info("  instagram_business_basic")
                info("  instagram_business_content_publish")
                return False

            if declined:
                warn(f"Declined permissions: {sorted(declined)}")

            ok("All required permissions granted.")
            return True

        else:
            err = data.get("error", {})
            fail(f"HTTP {resp.status_code}: {err.get('message', 'Unknown')}")
            return False

    except requests.RequestException as exc:
        fail(f"Request failed: {exc}")
        return False


def test_rate_limit(ig: dict) -> bool:
    """
    Check publishing rate limit status (100 posts / 24h).
    GET /{user_id}/content_publishing_limit
    """
    print("\n[4/5] Rate limit check -- GET /{user_id}/content_publishing_limit")
    print("      -" * 20)

    token = ig["access_token"]
    user_id = ig["user_id"]
    api_version = ig.get("api_version", "v24.0")
    host = ig.get("host", "graph.instagram.com")
    url = f"https://{host}/{api_version}/{user_id}/content_publishing_limit"

    params = {
        "fields": "config,quota_usage",
        "access_token": token,
    }

    try:
        resp = requests.get(url, params=params, timeout=15)
        data = resp.json()

        if resp.status_code == 200:
            items = data.get("data", [])
            if items:
                cfg = items[0].get("config", {})
                usage = items[0].get("quota_usage", "N/A")
                quota_total = cfg.get("quota_total", 100)
                quota_duration = cfg.get("quota_duration", 86400)
                remaining = quota_total - (usage if isinstance(usage, int) else 0)

                ok(f"Quota: {usage}/{quota_total} used in last {quota_duration//3600}h")
                ok(f"Remaining: {remaining} posts available")

                if isinstance(usage, int) and usage >= quota_total:
                    warn("Rate limit reached! Wait before publishing.")
                    return False
            else:
                ok("Rate limit data returned (no usage yet).")
            return True

        else:
            err = data.get("error", {})
            fail(f"HTTP {resp.status_code}: {err.get('message', 'Unknown')}")
            # This might fail if the endpoint needs business-level access
            info("Note: rate limit check requires instagram_business_content_publish permission.")
            return False

    except requests.RequestException as exc:
        fail(f"Request failed: {exc}")
        return False


def test_dry_run_container(ig: dict) -> bool:
    """
    Dry run: attempt to create a container with a known test image.
    This WILL create a container (not published), testing the full Step 1 flow.
    The container expires in 24 hours if not published -- no harm done.
    """
    print("\n[5/5] Dry-run container creation (Step 1 only, NOT published)")
    print("      -" * 20)

    # Public test image (Meta will cURL this server-side)
    TEST_IMAGE_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Cat03.jpg/1200px-Cat03.jpg"

    print(f"  Using test image: {TEST_IMAGE_URL}")

    answer = input("\n  Run dry-run container creation? This calls the real API. [y/N] ").strip().lower()
    if answer != "y":
        info("Skipped. Run again and type 'y' to test container creation.")
        return True  # Not a failure, just skipped

    token = ig["access_token"]
    user_id = ig["user_id"]
    api_version = ig.get("api_version", "v24.0")
    host = ig.get("host", "graph.instagram.com")
    url = f"https://{host}/{api_version}/{user_id}/media"

    params = {
        "image_url": TEST_IMAGE_URL,
        "caption": "[API test -- do not publish]",
        "media_type": "IMAGE",
        "access_token": token,
    }

    try:
        resp = requests.post(url, params=params, timeout=30)
        data = resp.json()

        if resp.status_code == 200:
            container_id = data.get("id")
            ok(f"Container created successfully!")
            ok(f"Container ID: {container_id}")
            ok(f"(Container will expire in 24h if not published -- safe to ignore)")
            return True
        else:
            err = data.get("error", {})
            fail(f"HTTP {resp.status_code} -- {err.get('message', 'Unknown')}")
            info(f"Error type:  {err.get('type', 'N/A')}")
            info(f"Error code:  {err.get('code', 'N/A')}")
            return False

    except requests.RequestException as exc:
        fail(f"Request failed: {exc}")
        return False


# -- Main ---------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Instagram Graph API diagnostic")
    parser.add_argument(
        "--config", "-c",
        default=os.environ.get("CONFIG_FILE_PATH", "config.json"),
        help="Path to config.json (default: config.json or $CONFIG_FILE_PATH)",
    )
    parser.add_argument(
        "--skip-dryrun", action="store_true",
        help="Skip the container dry-run test (test 5)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  Instagram Graph API Diagnostic")
    print(f"  Config: {args.config}")
    print("=" * 60)

    config = load_config(args.config)
    ig = config.get("instagram", {})

    results = {}

    results["config"]      = test_config(ig)
    if not results["config"]:
        print("\n[STOP] Fix config.json first, then re-run.")
        sys.exit(1)

    results["token"]       = test_token_validity(ig)
    results["permissions"] = test_permissions(ig) if results["token"] else False
    results["rate_limit"]  = test_rate_limit(ig)  if results["token"] else False

    if not args.skip_dryrun and results.get("permissions"):
        results["dry_run"] = test_dry_run_container(ig)
    else:
        results["dry_run"] = None  # skipped

    # -- Summary --
    print("\n" + "=" * 60)
    print("  DIAGNOSTIC SUMMARY")
    print("=" * 60)

    status_map = {True: "[PASS]", False: "[FAIL]", None: "[SKIP]"}
    labels = [
        ("config",      "Config completeness"),
        ("token",       "Token validity (/me)"),
        ("permissions", "Permissions check"),
        ("rate_limit",  "Rate limit check"),
        ("dry_run",     "Container creation (dry-run)"),
    ]
    all_pass = True
    for key, label in labels:
        v = results.get(key)
        print(f"  {status_map[v]}  {label}")
        if v is False:
            all_pass = False

    print("=" * 60)

    if all_pass:
        print("  All checks passed! Instagram API is ready.")
        print("  Run: python post_to_social.py  (set mode='instagram_only' or 'dual')")
    else:
        print("  Some checks failed. Fix the issues above, then re-run.")
        sys.exit(1)


if __name__ == "__main__":
    main()
