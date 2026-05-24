#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Social Media Auto-Post Script
Supports: Instagram Graph API + Threads API
Dual-platform posting with unified SocialMediaAPI interface

Flow:
  Threads  -> Step 1: POST /{user_id}/threads  -> Step 2: POST /{user_id}/threads_publish
  Instagram -> Step 1: POST /{user_id}/media    -> (poll status) -> Step 2: POST /{user_id}/media_publish

Usage:
  python post_to_social.py                    # runs main() example
  CONFIG_FILE_PATH=/path/config.json python post_to_social.py
"""

import json
import os
import sys
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests


# ==============================================================================
# Abstract Base Class
# ==============================================================================

class SocialMediaAPI(ABC):
    """Abstract base class for all social media platform clients."""

    @abstractmethod
    def post(self, text: str, **kwargs) -> Optional[str]:
        """
        Publish content to the platform.
        Returns post_id / media_id string on success, None on failure.
        """
        pass

    def _log_api_error(self, response: requests.Response, platform: str) -> None:
        """Unified error logger for API error responses."""
        try:
            body = response.json()
            err = body.get("error", {})
            print(f"  [ERROR] {platform} API error:")
            print(f"    HTTP status : {response.status_code}")
            print(f"    Message     : {err.get('message', 'Unknown')}")
            print(f"    Code        : {err.get('code', 'N/A')}")
            print(f"    Type        : {err.get('type', 'N/A')}")
            fbtrace = err.get("fbtrace_id")
            if fbtrace:
                print(f"    fbtrace_id  : {fbtrace}")
        except Exception:
            print(f"  [ERROR] {platform} HTTP {response.status_code}: {response.text[:300]}")


# ==============================================================================
# Threads API
# ==============================================================================

class ThreadsAPI(SocialMediaAPI):
    """
    Threads API client.
    Two-step process:
      Step 1 -> POST /{user_id}/threads       -> container_id
      Step 2 -> POST /{user_id}/threads_publish -> post_id
    """

    BASE_URL = "https://graph.threads.net/v1.0"
    MAX_TEXT_LEN = 500

    def __init__(self, user_id: str, access_token: str):
        self.user_id = user_id
        self.access_token = access_token

    # -- Step 1 -------------------------------------------------------------

    def create_container(
        self,
        text: str,
        media_type: str = "TEXT",
        image_url: Optional[str] = None,
    ) -> Optional[str]:
        """Create a Threads media container. Returns creation_id."""
        url = f"{self.BASE_URL}/{self.user_id}/threads"
        params: Dict[str, Any] = {
            "media_type": media_type,
            "text": text,
            "access_token": self.access_token,
        }
        if image_url:
            params["image_url"] = image_url

        print(f"  [Threads] Step 1 -- creating container (type={media_type}, {len(text)} chars)...")

        try:
            resp = requests.post(url, params=params, timeout=15)
            if resp.status_code == 200:
                cid = resp.json().get("id")
                print(f"  [Threads] [OK] Container created: {cid}")
                return cid
            self._log_api_error(resp, "Threads")
            return None
        except requests.RequestException as exc:
            print(f"  [ERROR] Threads container request failed: {exc}")
            return None

    # -- Step 2 -------------------------------------------------------------

    def publish_container(self, creation_id: str) -> Optional[str]:
        """Publish a Threads container. Returns post_id."""
        url = f"{self.BASE_URL}/{self.user_id}/threads_publish"
        params = {
            "creation_id": creation_id,
            "access_token": self.access_token,
        }

        print(f"  [Threads] Step 2 -- publishing container {creation_id}...")

        try:
            resp = requests.post(url, params=params, timeout=15)
            if resp.status_code == 200:
                pid = resp.json().get("id")
                print(f"  [Threads] [OK] Published! Post ID: {pid}")
                return pid
            self._log_api_error(resp, "Threads")
            return None
        except requests.RequestException as exc:
            print(f"  [ERROR] Threads publish request failed: {exc}")
            return None

    # -- Public API ----------------------------------------------------------

    def post(
        self,
        text: str,
        media_type: str = "TEXT",
        image_url: Optional[str] = None,
        **kwargs,
    ) -> Optional[str]:
        """
        Full Threads post: create container -> publish.
        text: max 500 chars (split into threads if longer -- caller's responsibility).
        Returns post_id or None.
        """
        if len(text) > self.MAX_TEXT_LEN:
            print(f"  [WARN] Threads text {len(text)} chars exceeds {self.MAX_TEXT_LEN} limit.")
            print(f"         Truncating. Consider splitting into a thread instead.")
            text = text[: self.MAX_TEXT_LEN - 3] + "..."

        creation_id = self.create_container(text, media_type, image_url)
        if not creation_id:
            return None
        return self.publish_container(creation_id)

    def post_thread(
        self,
        parts: List[str],
        media_type: str = "TEXT",
    ) -> Optional[str]:
        """
        Post a multi-part Threads thread (串).
        parts[0] is the root post, the rest are replies.
        Returns the root post_id or None on failure.
        """
        if not parts:
            return None

        print(f"  [Threads] Posting thread with {len(parts)} part(s)...")
        root_id = self.post(parts[0], media_type=media_type)
        if not root_id:
            print("  [ERROR] Failed to post root thread. Stopping.")
            return None

        for i, part in enumerate(parts[1:], start=2):
            time.sleep(2)  # 2-3s between thread replies
            url = f"{self.BASE_URL}/{self.user_id}/threads"
            params = {
                "media_type": "TEXT",
                "text": part,
                "reply_to": root_id,
                "access_token": self.access_token,
            }
            try:
                resp = requests.post(url, params=params, timeout=15)
                if resp.status_code == 200:
                    cid = resp.json().get("id")
                    # Publish the reply container
                    time.sleep(1)
                    pub_url = f"{self.BASE_URL}/{self.user_id}/threads_publish"
                    pub_resp = requests.post(
                        pub_url,
                        params={"creation_id": cid, "access_token": self.access_token},
                        timeout=15,
                    )
                    if pub_resp.status_code == 200:
                        print(f"  [Threads] [OK] Part {i}/{len(parts)} published")
                    else:
                        self._log_api_error(pub_resp, "Threads")
                else:
                    self._log_api_error(resp, "Threads")
            except requests.RequestException as exc:
                print(f"  [ERROR] Thread part {i} failed: {exc}")

        return root_id


# ==============================================================================
# Instagram Graph API
# ==============================================================================

class InstagramAPI(SocialMediaAPI):
    """
    Instagram Graph API client.
    Two-step process:
      Step 1 -> POST /{ig_user_id}/media         -> container_id
      (poll) -> GET  /{container_id}?fields=status_code
      Step 2 -> POST /{ig_user_id}/media_publish -> media_id

    Requirements:
      - Instagram Business or Creator account
      - Access token with: instagram_business_basic + instagram_business_content_publish
      - image_url must be on a publicly accessible server (Meta will cURL it)
      - Only JPEG images are fully supported (PNG accepted but may be converted)
    """

    MAX_CAPTION_LEN = 2200
    # Container status constants
    STATUS_FINISHED    = "FINISHED"
    STATUS_IN_PROGRESS = "IN_PROGRESS"
    STATUS_ERROR       = "ERROR"
    STATUS_EXPIRED     = "EXPIRED"
    STATUS_PUBLISHED   = "PUBLISHED"

    def __init__(
        self,
        user_id: str,
        access_token: str,
        api_version: str = "v24.0",
        host: str = "graph.instagram.com",
    ):
        self.user_id = user_id
        self.access_token = access_token
        self.base_url = f"https://{host}/{api_version}"

    # -- Step 1 -------------------------------------------------------------

    def create_container(
        self,
        caption: str,
        image_url: str,
        media_type: str = "IMAGE",
    ) -> Optional[str]:
        """
        Upload media and create IG container.
        image_url MUST be publicly accessible -- Meta cURLs it server-side.
        Returns container_id.
        """
        url = f"{self.base_url}/{self.user_id}/media"
        params = {
            "image_url": image_url,
            "caption": caption,
            "media_type": media_type,
            "access_token": self.access_token,
        }

        print(f"  [Instagram] Step 1 -- creating media container...")
        print(f"    Image URL : {image_url}")
        print(f"    Caption   : {len(caption)} chars")

        try:
            resp = requests.post(url, params=params, timeout=30)
            if resp.status_code == 200:
                cid = resp.json().get("id")
                print(f"  [Instagram] [OK] Container created: {cid}")
                return cid
            self._log_api_error(resp, "Instagram")
            return None
        except requests.RequestException as exc:
            print(f"  [ERROR] Instagram container request failed: {exc}")
            return None

    # -- Status Check --------------------------------------------------------

    def get_container_status(self, container_id: str) -> str:
        """
        Query container publishing status.
        Returns one of: FINISHED | IN_PROGRESS | ERROR | EXPIRED | PUBLISHED
        """
        url = f"{self.base_url}/{container_id}"
        params = {"fields": "status_code", "access_token": self.access_token}
        try:
            resp = requests.get(url, params=params, timeout=15)
            if resp.status_code == 200:
                return resp.json().get("status_code", "UNKNOWN")
            return "ERROR"
        except requests.RequestException:
            return "ERROR"

    def wait_for_container(
        self,
        container_id: str,
        max_polls: int = 6,
        poll_interval: int = 10,
    ) -> bool:
        """
        Poll container status until FINISHED (or failure/timeout).
        For images: usually FINISHED within 1-2 polls.
        For videos: may need all 6 polls (~1 min total).
        Meta recommends: once/min, <=5 min.
        """
        print(f"  [Instagram] Polling container {container_id} for readiness...")

        for attempt in range(1, max_polls + 1):
            status = self.get_container_status(container_id)
            print(f"    Poll {attempt}/{max_polls}: status = {status}")

            if status == self.STATUS_FINISHED:
                print(f"  [Instagram] [OK] Container ready!")
                return True
            if status == self.STATUS_PUBLISHED:
                print(f"  [Instagram] Container already published.")
                return True
            if status in (self.STATUS_ERROR, self.STATUS_EXPIRED):
                print(f"  [Instagram] [FAIL] Container failed: {status}")
                return False
            # IN_PROGRESS or UNKNOWN -> keep polling
            if attempt < max_polls:
                print(f"    Waiting {poll_interval}s before next poll...")
                time.sleep(poll_interval)

        print(f"  [Instagram] [FAIL] Container not ready after {max_polls} polls.")
        return False

    # -- Step 2 -------------------------------------------------------------

    def publish_container(self, container_id: str) -> Optional[str]:
        """
        Publish a ready container.
        Returns final media_id (published post ID) or None.
        """
        url = f"{self.base_url}/{self.user_id}/media_publish"
        params = {
            "creation_id": container_id,
            "access_token": self.access_token,
        }

        print(f"  [Instagram] Step 2 -- publishing container {container_id}...")

        try:
            resp = requests.post(url, params=params, timeout=30)
            if resp.status_code == 200:
                mid = resp.json().get("id")
                print(f"  [Instagram] [OK] Published! Media ID: {mid}")
                return mid
            self._log_api_error(resp, "Instagram")
            return None
        except requests.RequestException as exc:
            print(f"  [ERROR] Instagram publish request failed: {exc}")
            return None

    # -- Rate Limit Check ----------------------------------------------------

    def get_rate_limit(self) -> Dict[str, Any]:
        """
        Check publishing rate limit (100 posts per 24h rolling window).
        Returns dict with config + quota_usage, or {"error": ...}.
        """
        url = f"{self.base_url}/{self.user_id}/content_publishing_limit"
        params = {
            "fields": "config,quota_usage",
            "access_token": self.access_token,
        }
        try:
            resp = requests.get(url, params=params, timeout=15)
            if resp.status_code == 200:
                return resp.json()
            return {"error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
        except requests.RequestException as exc:
            return {"error": str(exc)}

    # -- Public API ----------------------------------------------------------

    def post(
        self,
        text: str,
        image_url: Optional[str] = None,
        check_status: bool = True,
        **kwargs,
    ) -> Optional[str]:
        """
        Full Instagram post: create container -> (poll status) -> publish.

        text       : Caption text (max 2200 chars, hashtags at end).
        image_url  : Required. Publicly accessible URL (JPEG preferred).
        check_status: Poll container status before publishing (recommended).

        Returns media_id string or None.
        """
        # -- Guard: image required --
        if not image_url:
            print("  [ERROR] Instagram requires image_url for feed posts.")
            print("    Options:")
            print("    (A) Provide a public image_url parameter")
            print("    (B) Skip Instagram, post Threads only")
            print("    (C) Use Threads (supports text-only)")
            return None

        # -- Guard: caption length --
        caption = text
        if len(caption) > self.MAX_CAPTION_LEN:
            print(f"  [WARN] Caption {len(caption)} chars > {self.MAX_CAPTION_LEN} limit. Truncating.")
            caption = caption[: self.MAX_CAPTION_LEN - 3] + "..."

        # Step 1: Create container
        container_id = self.create_container(caption, image_url)
        if not container_id:
            return None

        # Poll status (recommended even for images)
        if check_status:
            # Image containers usually finish in < 5s; give a short initial wait
            time.sleep(3)
            if not self.wait_for_container(container_id):
                print("  [ERROR] Container not ready. Aborting publish.")
                return None

        # Step 2: Publish
        return self.publish_container(container_id)


# ==============================================================================
# Social Post Manager -- Dual-Platform Coordinator
# ==============================================================================

class SocialPostManager:
    """
    Loads config.json and orchestrates posting to Instagram + Threads.

    Usage:
        manager = SocialPostManager("config.json")
        manager.post_to_threads("Your text here")
        manager.post_to_instagram("Caption", "https://example.com/image.jpg")
        manager.post_to_both(threads_text=..., ig_caption=..., image_url=...)
    """

    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.threads: Optional[ThreadsAPI] = None
        self.instagram: Optional[InstagramAPI] = None
        self._init_clients()

    # -- Config --------------------------------------------------------------

    def _load_config(self) -> dict:
        try:
            with open(self.config_path, "r", encoding="utf-8-sig") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"[ERROR] Config not found: {self.config_path}")
            sys.exit(1)
        except json.JSONDecodeError as exc:
            print(f"[ERROR] Invalid JSON in config: {exc}")
            sys.exit(1)

    def _is_placeholder(self, value: str, is_user_id: bool = False) -> bool:
        """Detect placeholder / example tokens."""
        if not value:
            return True
        # User IDs are typically 17-21 digit numbers
        # Tokens are 100+ chars and start with IGAA or THAA
        min_len = 10 if is_user_id else 50
        if len(value) < min_len:
            return True
        placeholders = ["YourLong", "YOUR_", "abc123", "example", "PLACEHOLDER"]
        return any(p.lower() in value.lower() for p in placeholders)

    def _init_clients(self):
        """Initialize API clients from config, skipping incomplete/placeholder configs."""
        print("[Init] Loading API clients from config...")

        # -- Threads --
        t = self.config.get("threads", {})
        t_uid = t.get("user_id", "")
        t_tok = t.get("access_token", "")
        if t_uid and t_tok and not self._is_placeholder(t_tok) and not self._is_placeholder(t_uid, is_user_id=True):
            self.threads = ThreadsAPI(user_id=t_uid, access_token=t_tok)
            print(f"  [OK] Threads   -> user_id={t_uid}")
        else:
            print(f"  [WARN]  Threads   -> config incomplete or placeholder token. Disabled.")

        # -- Instagram --
        ig = self.config.get("instagram", {})
        ig_uid = ig.get("user_id", "")
        ig_tok = ig.get("access_token", "")
        if ig_uid and ig_tok and not self._is_placeholder(ig_tok) and not self._is_placeholder(ig_uid, is_user_id=True):
            self.instagram = InstagramAPI(
                user_id=ig_uid,
                access_token=ig_tok,
                api_version=ig.get("api_version", "v24.0"),
                host=ig.get("host", "graph.instagram.com"),
            )
            print(f"  [OK] Instagram -> user_id={ig_uid}, host={ig.get('host','graph.instagram.com')}")
        else:
            print(f"  [WARN]  Instagram -> config incomplete or placeholder token. Disabled.")
            print(f"      Set instagram.user_id + instagram.access_token in config.json")
            print(f"      See references/instagram.md for setup instructions.")

        print()

    # -- Individual Platform Methods -----------------------------------------

    def post_to_threads(
        self,
        text: str,
        media_type: str = "TEXT",
        image_url: Optional[str] = None,
    ) -> Optional[str]:
        """Post to Threads only. Returns post_id or None."""
        if not self.threads:
            print("[ERROR] Threads API not configured. Check config.json.")
            return None
        return self.threads.post(text, media_type=media_type, image_url=image_url)

    def post_to_instagram(
        self,
        caption: str,
        image_url: str,
    ) -> Optional[str]:
        """Post to Instagram only (image required). Returns media_id or None."""
        if not self.instagram:
            print("[ERROR] Instagram API not configured. See references/instagram.md.")
            return None
        return self.instagram.post(caption, image_url=image_url)

    # -- Dual Platform --------------------------------------------------------

    def post_to_both(
        self,
        threads_text: str,
        ig_caption: str,
        image_url: str,
        threads_media_type: str = "TEXT",
        threads_image_url: Optional[str] = None,
        ig_first: bool = False,
    ) -> Dict[str, Optional[str]]:
        """
        Post to both Instagram and Threads.
        Each platform gets its own content (different tone/length per SKILL.md rules).

        Args:
            threads_text       : Threads content (<=500 chars, F19 style)
            ig_caption         : Instagram caption (<=2200 chars, with hashtags)
            image_url          : Publicly accessible image URL (required for Instagram)
            threads_media_type : "TEXT" or "IMAGE" for Threads post
            threads_image_url  : Optional separate image for Threads (falls back to image_url)
            ig_first           : Post to Instagram first (default: Threads first)

        Returns:
            {"threads": post_id_or_None, "instagram": media_id_or_None}
        """
        results: Dict[str, Optional[str]] = {"threads": None, "instagram": None}

        print("\n" + "=" * 70)
        print("  DUAL-PLATFORM POST")
        print("=" * 70)

        platforms = (
            [("instagram", 1), ("threads", 2)]
            if ig_first
            else [("threads", 1), ("instagram", 2)]
        )

        for platform, order in platforms:
            print(f"\n[{order}/2] {platform.upper()}")
            print("-" * 40)

            if platform == "threads":
                t_img = threads_image_url or (
                    image_url if threads_media_type == "IMAGE" else None
                )
                results["threads"] = self.post_to_threads(
                    threads_text,
                    media_type=threads_media_type,
                    image_url=t_img,
                )
            else:
                results["instagram"] = self.post_to_instagram(ig_caption, image_url)

            # Brief buffer between platforms
            if order == 1:
                time.sleep(3)

        # -- Summary ----------------------------------------------------------
        print("\n" + "=" * 70)
        print("  SUMMARY")
        print("=" * 70)

        t_id = results["threads"]
        ig_id = results["instagram"]

        if t_id:
            print(f"  [OK] Threads   -> https://www.threads.net/post/{t_id}")
        else:
            print("  [FAIL] Threads   -> FAILED (check token + config)")

        if ig_id:
            print(f"  [OK] Instagram -> Media ID: {ig_id}")
            print(f"               (View in Meta Business Suite or Instagram app)")
        else:
            print("  [FAIL] Instagram -> FAILED (check token / image_url / permissions)")

        print("=" * 70)
        return results

    # -- Diagnostics ---------------------------------------------------------

    def check_instagram_rate_limit(self) -> None:
        """Print Instagram publishing rate limit status."""
        if not self.instagram:
            print("[ERROR] Instagram API not configured.")
            return
        info = self.instagram.get_rate_limit()
        print("[Instagram Rate Limit]")
        print(json.dumps(info, indent=2))


# ==============================================================================
# Config Helpers
# ==============================================================================

def update_instagram_in_config(
    config_path: str = "config.json",
    user_id: Optional[str] = None,
    access_token: Optional[str] = None,
    app_id: Optional[str] = None,
    app_secret: Optional[str] = None,
    api_version: str = "v24.0",
    host: str = "graph.instagram.com",
) -> None:
    """
    Update instagram section in config.json.
    Run once after obtaining your Instagram User Access Token.

    Example:
        update_instagram_in_config(
            user_id="17841400000000000",
            access_token="IGAAxxxYourRealToken...",
            app_id="990908076790797",
        )
    """
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except FileNotFoundError:
        config = {}

    ig = config.setdefault("instagram", {})

    if user_id:
        ig["user_id"] = user_id
    if access_token:
        ig["access_token"] = access_token
        ig["expires_at"] = int(time.time()) + 5_184_000  # 60 days in seconds
    if app_id:
        ig["app_id"] = app_id
    if app_secret:
        ig["app_secret"] = app_secret

    ig.setdefault("api_version", api_version)
    ig.setdefault("host", host)
    ig.setdefault("token_type", "bearer")

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print(f"[OK] Instagram config updated in {config_path}")


# ==============================================================================
# Token Refresh Helpers
# ==============================================================================

def refresh_instagram_token(config_path: str = "config.json") -> bool:
    """
    Refresh Instagram long-lived access token (valid 60 days).
    Call this at least once every 60 days, or automate via cron.
    Endpoint: GET https://graph.instagram.com/refresh_access_token
              ?grant_type=ig_refresh_token&access_token=CURRENT_TOKEN
    """
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as exc:
        print(f"[ERROR] Cannot read config: {exc}")
        return False

    ig = config.get("instagram", {})
    token = ig.get("access_token", "")
    if not token or len(token) < 30:
        print("[ERROR] No valid Instagram access_token found in config.")
        return False

    print("[Instagram] Refreshing access token...")
    url = "https://graph.instagram.com/refresh_access_token"
    params = {"grant_type": "ig_refresh_token", "access_token": token}

    try:
        resp = requests.get(url, params=params, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            new_token = data.get("access_token")
            expires_in = data.get("expires_in", 5_184_000)
            new_expires_at = int(time.time()) + expires_in

            config["instagram"]["access_token"] = new_token
            config["instagram"]["expires_at"] = new_expires_at

            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            print(f"  [OK] Token refreshed. Valid until: "
                  f"{datetime.fromtimestamp(new_expires_at).strftime('%Y-%m-%d')}")
            return True
        else:
            try:
                err = resp.json().get("error", {}).get("message", resp.text)
            except Exception:
                err = resp.text
            print(f"  [ERROR] Refresh failed: {err}")
            return False
    except requests.RequestException as exc:
        print(f"  [ERROR] Request failed: {exc}")
        return False


def refresh_threads_token(config_path: str = "config.json") -> bool:
    """
    Refresh Threads long-lived access token (valid 60 days).
    Endpoint: GET https://graph.threads.net/refresh_access_token
              ?grant_type=th_refresh_token&access_token=CURRENT_TOKEN
    """
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as exc:
        print(f"[ERROR] Cannot read config: {exc}")
        return False

    t = config.get("threads", {})
    token = t.get("access_token", "")
    if not token or len(token) < 30:
        print("[ERROR] No valid Threads access_token found in config.")
        return False

    print("[Threads] Refreshing access token...")
    url = "https://graph.threads.net/refresh_access_token"
    params = {"grant_type": "th_refresh_token", "access_token": token}

    try:
        resp = requests.get(url, params=params, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            new_token = data.get("access_token")
            expires_in = data.get("expires_in", 5_184_000)
            new_expires_at = int(time.time()) + expires_in

            config["threads"]["access_token"] = new_token
            config["threads"]["expires_at"] = new_expires_at

            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            print(f"  [OK] Token refreshed. Valid until: "
                  f"{datetime.fromtimestamp(new_expires_at).strftime('%Y-%m-%d')}")
            return True
        else:
            try:
                err = resp.json().get("error", {}).get("message", resp.text)
            except Exception:
                err = resp.text
            print(f"  [ERROR] Refresh failed: {err}")
            return False
    except requests.RequestException as exc:
        print(f"  [ERROR] Request failed: {exc}")
        return False


# ==============================================================================
# Main -- Example Usage
# ==============================================================================

def main():
    """
    Example dual-platform post.
    Edit the content variables and image_url before running.
    Set CONFIG_FILE_PATH env var if config.json is not in current directory.
    """
    config_path = os.environ.get("CONFIG_FILE_PATH", "config.json")
    manager = SocialPostManager(config_path)

    # -- Content --------------------------------------------------------------
    # Threads: short, punchy, F19 style (60-150 chars, 1 paragraph, no line breaks)
    threads_text = (
        "欠債 180 萬的時候,我想過最壞的打算,後來才知道連最基本的選項都不懂,"
        "三十歲那年利率是 18%!"
    )

    # Instagram: longer caption with hashtags at the end, hook in first 125 chars
    instagram_caption = (
        "欠債 180 萬的時候,我想過最壞的打算.\n"
        "後來才知道,我連最基本的選項都不知道.\n"
        "三十歲那年,我的利率是 18%.\n\n"
        '這一篇不是在說理財,是在說"資訊不對稱"有多貴.\n\n'
        "#個人理財 #財務自由 #真實故事 #債務整合 #理財規劃"
    )

    # Image URL: must be publicly accessible (Meta cURLs it server-side)
    # Replace with your actual image URL before running
    image_url = "https://example.com/your-image.jpg"  # <- REPLACE THIS

    # -- Choose posting mode --------------------------------------------------
    # "threads_only" | "instagram_only" | "dual"
    mode = "threads_only"  # Change to "dual" once Instagram token is configured

    if mode == "threads_only":
        post_id = manager.post_to_threads(threads_text)
        if post_id:
            print(f"\n[OK] Threads: https://www.threads.net/post/{post_id}")
        else:
            print("\n[FAIL] Threads post failed.")
            sys.exit(1)

    elif mode == "instagram_only":
        media_id = manager.post_to_instagram(instagram_caption, image_url)
        if media_id:
            print(f"\n[OK] Instagram media_id: {media_id}")
        else:
            print("\n[FAIL] Instagram post failed.")
            sys.exit(1)

    elif mode == "dual":
        results = manager.post_to_both(
            threads_text=threads_text,
            ig_caption=instagram_caption,
            image_url=image_url,
            threads_media_type="TEXT",   # Threads posts text-only
        )
        if not results["threads"] and not results["instagram"]:
            sys.exit(1)

    else:
        print(f"[ERROR] Unknown mode: {mode}. Use 'threads_only', 'instagram_only', or 'dual'.")
        sys.exit(1)


if __name__ == "__main__":
    main()
