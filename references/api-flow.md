# API 發文流程完整指南

本檔案描述完整的 API 發文流程，包括認證、Token 管理、發文、與錯誤處理。

## 架構概覽

```
┌─────────────────────────────────────────┐
│  P2：生成 + 發佈（generate_and_publish）  │
└──────────────┬──────────────────────────┘
               │
        ┌──────▼──────────────────┐
        │ 讀取 config.json        │
        │ (Instagram + Threads)   │
        └──────┬──────────────────┘
               │
        ┌──────▼──────────────────┐
        │ 檢查 Token 有效期       │
        │ (auto-refresh if < 5m)  │
        └──────┬──────────────────┘
               │
        ┌──────▼──────────────────┐
        │ Instagram 發文          │
        │ (Graph API)             │
        └──────┬──────────────────┘
               │
        ┌──────▼──────────────────┐
        │ Threads 發文            │
        │ (Meta API)              │
        └──────┬──────────────────┘
               │
        ┌──────▼──────────────────┐
        │ 更新 content_plan.md    │
        │ (記錄連結、日期)        │
        └──────────────────────────┘
```

## 檔案結構

### config.json 格式

```json
{
  "instagram": {
    "user_id": "17841400000000",
    "app_id": "123456789",
    "app_secret": "abc123def456xyz789...",
    "access_token": "IGAABXz...",
    "token_type": "bearer",
    "expires_at": 1234567890
  },
  "threads": {
    "user_id": "123456789",
    "app_id": "123456789",
    "app_secret": "abc123def456xyz789...",
    "access_token": "IGAABXz...",
    "token_type": "bearer",
    "expires_at": 1234567890
  },
  "token_refresh": {
    "auto_refresh": true,
    "refresh_before_expiry_minutes": 5
  }
}
```

- **user_id**：Instagram Business Account ID（不是應用 ID）
- **access_token**：Long-lived Access Token（有效期 60 天）
- **expires_at**：Unix timestamp（Token 過期時刻）
- **auto_refresh**：是否自動刷新（應總是 true）

### .gitignore 保護

```
config.json
.env
.env.local
.secrets/
style_profile.md
content_plan.md
```

**重要**：絕不上傳 `config.json`（含密鑰）或個人檔案。

## Token 管理

### 有效期檢查

每次發文前，檢查 Token 是否即將過期：

```python
import json
import time
from datetime import timedelta

with open('config.json', 'r') as f:
    config = json.load(f)

platform = 'instagram'  # 或 'threads'
expires_at = config[platform]['expires_at']
now = int(time.time())

# 檢查是否需要刷新
refresh_threshold = config['token_refresh']['refresh_before_expiry_minutes'] * 60
if (expires_at - now) < refresh_threshold:
    print(f"Token 即將過期，執行刷新...")
    refresh_token(platform)
```

### Token 刷新流程（Instagram）

```python
import requests

def refresh_instagram_token(config):
    url = "https://graph.instagram.com/refresh_access_token"
    
    params = {
        'grant_type': 'ig_refresh_token',
        'access_token': config['instagram']['access_token']
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        config['instagram']['access_token'] = data['access_token']
        config['instagram']['expires_at'] = int(time.time()) + data['expires_in']
        
        # 保存更新
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        return True
    else:
        print(f"Token 刷新失敗：{response.text}")
        return False
```

### Token 刷新流程（Threads）

Threads 與 Instagram 共享同一 Token（因為 Meta 一致性），刷新流程相同。

## 發文流程（Instagram）

### Step 1：準備媒體

用戶提供圖片後：

```python
def upload_instagram_image(config, image_path, caption):
    """
    上傳圖片到 Instagram，返回 media_id
    """
    url = f"https://graph.instagram.com/v24.0/{config['instagram']['user_id']}/media"
    
    # 讀取圖片（支援 JPG, PNG, GIF）
    with open(image_path, 'rb') as f:
        files = {'file': f}
        
        data = {
            'caption': caption,
            'media_type': 'IMAGE',
            'access_token': config['instagram']['access_token']
        }
        
        response = requests.post(url, files=files, data=data)
    
    if response.status_code == 200:
        return response.json()['id']
    else:
        raise Exception(f"上傳失敗：{response.text}")
```

### Step 2：發佈貼文

```python
def publish_instagram_post(config, media_id):
    """
    發佈 Media Container 到 Feed
    """
    url = f"https://graph.instagram.com/v24.0/{config['instagram']['user_id']}/media_publish"
    
    data = {
        'creation_id': media_id,
        'access_token': config['instagram']['access_token']
    }
    
    response = requests.post(url, data=data)
    
    if response.status_code == 200:
        post_id = response.json()['id']
        # 構組連結（可選）
        shortcode = get_shortcode(config, post_id)
        post_url = f"https://www.instagram.com/p/{shortcode}/"
        return post_url
    else:
        raise Exception(f"發佈失敗：{response.text}")
```

### Step 3：取得發文連結

```python
def get_shortcode(config, post_id):
    """
    從 post_id 查詢 shortcode（Instagram 短代碼）
    """
    url = f"https://graph.instagram.com/v24.0/{post_id}"
    
    params = {
        'fields': 'shortcode',
        'access_token': config['instagram']['access_token']
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        return response.json().get('shortcode')
    else:
        # Fallback：直接用 post_id
        return post_id
```

## 發文流程（Threads）

### Step 1：單篇貼文（< 500 字）

```python
def publish_threads_post(config, text):
    """
    發佈單則 Threads 貼文
    """
    url = f"https://graph.threads.net/v1.0/{config['threads']['user_id']}/threads"
    
    data = {
        'text': text,
        'media_type': 'TEXT',
        'access_token': config['threads']['access_token']
    }
    
    response = requests.post(url, data=data)
    
    if response.status_code == 200:
        post_id = response.json()['id']
        post_url = f"https://www.threads.net/@{config['threads']['username']}/post/{post_id}"
        return post_url
    else:
        raise Exception(f"發佈失敗：{response.text}")
```

### Step 2：分串貼文（> 500 字）

```python
def publish_threads_thread(config, text_list):
    """
    發佈分串 Threads（> 500 字分多則）
    
    Args:
        text_list: 每則的文本 list（每則 < 500 字）
    
    Returns:
        [post_url_1, post_url_2, ...]
    """
    parent_id = None
    urls = []
    
    for i, text in enumerate(text_list):
        url = f"https://graph.threads.net/v1.0/{config['threads']['user_id']}/threads"
        
        data = {
            'text': text,
            'media_type': 'TEXT',
            'access_token': config['threads']['access_token']
        }
        
        # 第二則及後續需指定 parent_id
        if parent_id:
            data['parent_id'] = parent_id
        
        response = requests.post(url, data=data)
        
        if response.status_code == 200:
            post_id = response.json()['id']
            post_url = f"https://www.threads.net/@{config['threads']['username']}/post/{post_id}"
            urls.append(post_url)
            
            # 第一則作為後續的 parent
            if i == 0:
                parent_id = post_id
        else:
            raise Exception(f"第 {i+1} 則發佈失敗：{response.text}")
    
    return urls
```

## 速率限制與等待

### Instagram

- 發文後等待 **30 秒**再發下一篇
- API 限制：通常 **200 請求/小時**（根據帳號等級調整）

### Threads

- 發文後等待 **10 秒**再發下一篇
- 分串時：每則間 **2-3 秒**

```python
import time

def post_with_cooldown(platform, post_fn, cooldown_seconds):
    """
    發文後自動等待冷卻時間
    """
    result = post_fn()
    time.sleep(cooldown_seconds)
    return result
```

## 錯誤處理與故障排除

### 常見錯誤

| 錯誤 | 原因 | 解決方案 |
|---|---|---|
| `401 Unauthorized` | Token 過期/無效 | 執行 token refresh，檢查 expires_at |
| `400 Bad Request` | 內容不合法 | 檢查字數、圖片格式、必填欄位 |
| `403 Forbidden` | 帳號權限不足 | 檢查是否升級到 Graph API（Instagram），Threads 帳號是否啟用 |
| `429 Too Many Requests` | 速率限制 | 等待後重試（加長冷卻時間）|
| `500 Server Error` | API 故障 | 稍候重試或告知使用者 |

### Token 失效時

若 `auto_refresh` 失敗（例如 API 回傳 invalid grant）：

1. **停止發文**，告知使用者 Token 已失效
2. **檢查 config.json** 中的 `expires_at` 是否遠早於當前時間
3. **重新授權**：見 `references/ig-graph-api-upgrade.md` 的「OAuth 流程」
4. **重新取得 Long-lived Access Token**，更新 config.json
5. 重試發文

### 發文失敗時

若單篇發文失敗但 Token 有效：

1. **記錄 API 回應**（具體錯誤信息）
2. **詢問使用者**：
   - 是否要修改內容（字數、圖片）重試
   - 是否改用其他平台
   - 是否保存草稿稍後重試
3. **暫不發佈到其他平台**（一平台失敗就停手，見 generate_and_publish.md）

## 安全實踐

### 密鑰保護

- `config.json` 必在 `.gitignore` 中
- 不要在代碼、log、聊天中暴露 token
- 若 token 意外暴露，立即在 Meta App Dashboard 重新核發

### 速率限制

- 不要濫發或測試發文（計入配額）
- 多帳號時共享配額；注意總流量

### 日誌記錄

發文時記錄：

```python
import logging

logging.basicConfig(filename='api_posts.log', level=logging.INFO)

logging.info(f"[{platform}] 發佈成功 - 連結：{post_url}")
logging.error(f"[{platform}] 發佈失敗 - 狀態碼：{status_code}，錯誤：{error_text}")
```

（日誌檔案含敏感信息，不要上傳 Git）

## 完整發文示例

```python
import json
import requests
import time

def publish_complete_flow(config, platform, content, image_path=None):
    """
    完整發文流程（檢查 Token → 上傳媒體 → 發佈 → 返回連結）
    """
    # Step 1：檢查並刷新 Token
    if should_refresh_token(config, platform):
        refresh_token(config, platform)
    
    # Step 2：發佈內容
    if platform == 'instagram':
        if not image_path:
            raise ValueError("Instagram 需要圖片")
        media_id = upload_instagram_image(config, image_path, content)
        post_url = publish_instagram_post(config, media_id)
        time.sleep(30)
    
    elif platform == 'threads':
        post_url = publish_threads_post(config, content)
        time.sleep(10)
    
    # Step 3：更新 content_plan.md（記錄連結）
    update_content_plan(platform, post_url)
    
    return post_url
```

## 相關檔案

- `api-integration.md`：Token 刷新與錯誤處理細節
- `ig-graph-api-upgrade.md`：Instagram Graph API 升級指南
- `instagram.md`：Instagram 發文參數與流程
- `threads.md`：Threads 發文參數與流程
- `.gitignore`：保護 config.json
