#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Threads API Post Script
Official Two-Step Publishing Process

Step 1: Create media container (POST /threads)
Step 2: Publish post (POST /threads_publish)
"""

import requests
import json
import sys
from typing import Tuple, Optional


class ThreadsAPI:
    """Threads API client for posting"""

    def __init__(self, user_id: str, access_token: str):
        self.user_id = user_id
        self.access_token = access_token
        self.base_url = "https://graph.threads.net/v1.0"

    def create_media_container(self, text: str, media_type: str = "TEXT",
                               image_url: Optional[str] = None) -> Optional[str]:
        """
        Step 1: Create media container
        Returns: creation_id (if successful)
        """
        url = f"{self.base_url}/{self.user_id}/threads"

        params = {
            "media_type": media_type,
            "text": text,
            "access_token": self.access_token
        }

        if image_url:
            params["image_url"] = image_url

        print(f"\n[Step 1] Creating media container...")
        print(f"  URL: {url}")
        print(f"  Media Type: {media_type}")
        print(f"  Text Length: {len(text)} chars")

        try:
            response = requests.post(url, params=params, timeout=10)
            result = response.json()

            if response.status_code == 200:
                creation_id = result.get("id")
                print(f"  [OK] Success! Creation ID: {creation_id}")
                return creation_id
            else:
                error = result.get("error", {})
                print(f"  [ERROR] {error.get('message')} (Code: {error.get('code')})")
                return None

        except Exception as e:
            print(f"  [ERROR] Exception: {e}")
            return None

    def publish_post(self, creation_id: str) -> Optional[str]:
        """
        Step 2: Publish post
        Returns: final post_id (if successful)
        """
        url = f"{self.base_url}/{self.user_id}/threads_publish"

        params = {
            "creation_id": creation_id,
            "access_token": self.access_token
        }

        print(f"\n[Step 2] Publishing post...")
        print(f"  URL: {url}")
        print(f"  Creation ID: {creation_id}")

        try:
            response = requests.post(url, params=params, timeout=10)
            result = response.json()

            if response.status_code == 200:
                post_id = result.get("id")
                print(f"  [OK] Success! Post ID: {post_id}")
                return post_id
            else:
                error = result.get("error", {})
                print(f"  [ERROR] {error.get('message')} (Code: {error.get('code')})")
                return None

        except Exception as e:
            print(f"  [ERROR] Exception: {e}")
            return None

    def post(self, text: str, media_type: str = "TEXT",
             image_url: Optional[str] = None) -> Optional[Tuple[str, str]]:
        """
        Complete post process: Create container + Publish
        Returns: (creation_id, post_id) if successful, None otherwise
        """
        print("=" * 70)
        print(f"POSTING TO THREADS")
        print("=" * 70)

        # Step 1
        creation_id = self.create_media_container(text, media_type, image_url)
        if not creation_id:
            print("\n[FAILED] Failed to create media container. Stopping.")
            return None

        # Step 2
        post_id = self.publish_post(creation_id)
        if not post_id:
            print("\n[FAILED] Failed to publish post.")
            return None

        print("\n" + "=" * 70)
        print(f"[SUCCESS] POST SUCCESSFUL!")
        print(f"  Creation ID: {creation_id}")
        print(f"  Post ID: {post_id}")
        print(f"  View: https://www.threads.net/@lena128_543/post/{post_id}")
        print("=" * 70)

        return (creation_id, post_id)


def load_config(config_path: str = "config.json") -> dict:
    """Load configuration from config.json"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {config_path} not found")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {config_path}")
        sys.exit(1)


def main():
    """Main function - Example usage"""

    # Load configuration
    config = load_config()

    # Initialize API client
    threads_config = config.get("threads", {})
    user_id = threads_config.get("user_id")
    access_token = threads_config.get("access_token")

    if not user_id or not access_token:
        print("Error: Missing user_id or access_token in config.json")
        sys.exit(1)

    # Create client
    api = ThreadsAPI(user_id, access_token)

    # Example: Post text
    post_text = "欠債 180 萬的時候，我想過最壞的打算。後來才知道，我連最基本的選項都不知道。三十歲那年，我的利率是 18%。"

    result = api.post(post_text, media_type="TEXT")

    if result:
        creation_id, post_id = result
        print(f"\nCreation ID: {creation_id}")
        print(f"Post ID: {post_id}")
    else:
        print("\nFailed to post")
        sys.exit(1)


if __name__ == "__main__":
    main()
