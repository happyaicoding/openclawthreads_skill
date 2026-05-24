# Instagram Graph API 發文指南

> **版本**: Graph API with Instagram Login  
> **Host**: `graph.instagram.com`  
> **腳本**: `post_to_social.py` → `InstagramAPI` 類別  
> **已驗證**: Threads API ✅ | Instagram Graph API ⬜（需設定 token）

---

## 重要限制

| 項目 | 規格 |
|---|---|
| 字數上限 | **2,200 字**（前 125 字顯示，之後折疊） |
| Hashtag | 建議 **5-15 個**，上限 30，置於文末空行隔開 |
| **圖片必須** | IG Feed 貼文一定要圖，純文字發不了 |
| 圖片格式 | **JPEG 優先**（PNG 接受但可能被轉換，不支援 HEIC/MPO） |
| 圖片來源 | 必須是**公開可訪問的 URL**（Meta 伺服器端 cURL 下載） |
| 速率限制 | 每 24 小時 **100 篇**（Carousel 算 1 篇） |
| 發文間隔 | 至少等 **30 秒** |
| 不支援 | Shopping tags、Filters、純文字貼文 |

---

## 前置條件

### 帳號要求

1. Instagram 帳號必須是 **Business 或 Creator 帳號**（不能是個人帳號）
   - Instagram App → 設定 → 帳號 → 切換為專業帳號
2. 連結到 **Facebook 粒子（Page）**（Graph API 要求）

### 權限要求

Meta App 需要以下 Permissions：

| Permission | 用途 |
|---|---|
| `instagram_business_basic` | 讀取帳號資訊 |
| `instagram_business_content_publish` | 發布貼文 |

### 取得 Instagram User Access Token

**步驟：**

```
1. 登入 Meta App Dashboard: https://developers.facebook.com/
   App ID: 990908076790797

2. 新增產品 → 選 "Instagram"
   → 設定 Business Login for Instagram

3. 設定 OAuth Redirect URI:
   https://developers.facebook.com/tools/explorer/
   （測試用）或你的後端 callback URL

4. 取得授權 URL:
   https://api.instagram.com/oauth/authorize
     ?client_id=990908076790797
     &redirect_uri=YOUR_REDIRECT_URI
     &scope=instagram_business_basic,instagram_business_content_publish
     &response_type=code

5. 用戶授權後取得 short-lived token (1小時)

6. 換成 long-lived token (60天):
   GET https://graph.instagram.com/access_token
     ?grant_type=ig_exchange_token
     &client_secret=YOUR_APP_SECRET
     &access_token=SHORT_LIVED_TOKEN

7. 取得 Instagram User ID:
   GET https://graph.instagram.com/me?fields=id,username&access_token=TOKEN
   → 記錄回傳的 "id"（這是 instagram.user_id）

8. 更新 config.json (見下方)
```

---

## 發文流程（API 版）

### 0. 環境檢查

確認 `config.json` 存在，且包含有效 Instagram 認證信息：

```json
{
  "instagram": {
    "user_id": "17841400000000000",
    "access_token": "IGAAxxxx...",
    "api_version": "v21.0",
    "host": "graph.instagram.com"
  }
}
```

### 1. Token 有效性檢查

```python
import time, json

with open("config.json") as f:
    config = json.load(f)

expires_at = config["instagram"].get("expires_at", 0)
remaining_days = (expires_at - time.time()) / 86400

if remaining_days < 7:
    print(f"⚠️ Token expires in {remaining_days:.0f} days — refresh soon")
    # run refresh_instagram_token() from post_to_social.py
```

### 2. 準備圖片

**重要**: IG API 需要公開 URL，不支援本機路徑或 base64。

```python
# 選項 A：已有公開 CDN URL
image_url = "https://cdn.example.com/images/post-cover.jpg"

# 選項 B：臨時上傳到圖床（如 Imgur、Cloudinary）
# 需另外實作圖片上傳邏輯

# 選項 C：自己的 hosting（Dropbox public link, Google Drive, etc.）
# 確保 URL 可直接下載（無需登入）
```

若無圖片：
- **(A)** 提供公開圖片 URL
- **(B)** 跳過 IG，只發 Threads（Threads 支援純文字）
- **(C)** 下次補圖再發

### 3. 建立 Media Container（Step 1）

```python
POST https://graph.instagram.com/v21.0/{USER_ID}/media
Query Parameters:
  image_url    = "https://example.com/image.jpg"
  caption      = "貼文內容 #hashtag1 #hashtag2"
  media_type   = "IMAGE"   ← 可省略（預設 IMAGE）
  access_token = "YOUR_TOKEN"

Response: { "id": "17889615814797922" }  ← container_id
```

**Python 範例：**

```python
import requests

url = f"https://graph.instagram.com/v21.0/{user_id}/media"
params = {
    "image_url": image_url,
    "caption": caption,
    "access_token": access_token,
}
resp = requests.post(url, params=params)
container_id = resp.json()["id"]
```

### 4. 檢查 Container 狀態（建議）

```python
GET https://graph.instagram.com/v21.0/{CONTAINER_ID}
Query Parameters:
  fields       = "status_code"
  access_token = "YOUR_TOKEN"

Response: { "status_code": "FINISHED", "id": "17889615814797922" }
```

| Status | 說明 |
|---|---|
| `FINISHED` | 可以發布 ✅ |
| `IN_PROGRESS` | 處理中，繼續等待 |
| `ERROR` | 失敗，需重新建立 container |
| `EXPIRED` | 24 小時過期，需重建 |
| `PUBLISHED` | 已發布 |

> 建議：每 10 秒 poll 一次，最多 6 次（1 分鐘）。圖片通常 < 5 秒完成。

### 5. 發布 Container（Step 2）

```python
POST https://graph.instagram.com/v21.0/{USER_ID}/media_publish
Query Parameters:
  creation_id  = "17889615814797922"   ← container_id from Step 1
  access_token = "YOUR_TOKEN"

Response: { "id": "17854360229135492" }  ← 最終 media_id（發布成功）
```

**Python 範例：**

```python
url = f"https://graph.instagram.com/v21.0/{user_id}/media_publish"
params = {
    "creation_id": container_id,
    "access_token": access_token,
}
resp = requests.post(url, params=params)
media_id = resp.json()["id"]
print(f"Published! Media ID: {media_id}")
```

---

## 使用 post_to_social.py 發文

### 單篇 Instagram

```python
from post_to_social import SocialPostManager

manager = SocialPostManager("config.json")

media_id = manager.post_to_instagram(
    caption="貼文內容\n\n#hashtag1 #hashtag2",
    image_url="https://example.com/image.jpg",
)
```

### 雙平台同時發文

```python
results = manager.post_to_both(
    threads_text="Threads 版文案（≤500字，口語短句）",
    ig_caption="IG 版文案（≤2200字，hashtag 結尾）",
    image_url="https://example.com/image.jpg",
    threads_media_type="TEXT",   # Threads 純文字
)
# results = {"threads": "post_id", "instagram": "media_id"}
```

---

## Token 管理

### 更新 config.json

```python
from post_to_social import update_instagram_in_config

update_instagram_in_config(
    config_path="config.json",
    user_id="17841400000000000",       # 從 /me endpoint 取得
    access_token="IGAAxxxx...",        # long-lived token
    app_id="990908076790797",
)
```

### 刷新 Token（每 60 天）

```python
from post_to_social import refresh_instagram_token
refresh_instagram_token("config.json")
```

或手動 curl：

```bash
curl "https://graph.instagram.com/refresh_access_token\
?grant_type=ig_refresh_token\
&access_token=YOUR_TOKEN"
```

---

## config.json Instagram 區段

```json
{
  "instagram": {
    "user_id": "17841400000000000",
    "app_id": "990908076790797",
    "app_secret": "YOUR_APP_SECRET",
    "access_token": "IGAAxxxx...",
    "token_type": "bearer",
    "expires_at": 1784604143,
    "api_version": "v21.0",
    "host": "graph.instagram.com"
  }
}
```

> ⚠️ `config.json` 已在 `.gitignore`。**永遠不要 commit config.json**。

---

## 錯誤處理

| 錯誤碼 | 狀況 | 處理方式 |
|---|---|---|
| 400 | 圖片格式不對 / 參數錯誤 | 確認圖片是 JPEG、URL 公開可訪問 |
| 401 | Token 過期或無效 | 執行 `refresh_instagram_token()` |
| 400 `#10` | 帳號無 `instagram_business_content_publish` 權限 | 重新授權，確認帳號是 Business/Creator |
| 400 `#36000` | Media 不是 IMAGE 格式 | 確認 `media_type=IMAGE` |
| 400 `#9007` | 圖片無法下載 | 確認 image_url 公開可訪問，非需登入 |
| 400 `#352` | Caption 超過 2200 字 | 截短 caption |
| 429 | 超過速率限制 | 等待後重試，查詢 `/content_publishing_limit` |
| 500/503 | Meta 伺服器故障 | 稍候重試 |

---

## 內容生成準則（IG 版）

- **前 125 字是 hook**：最重要，其他內容折疊後才顯示
- **換行排版**：IG 支援換行，善用空行分段
- **hashtag 末置**：正文後空一行再放 hashtag
- **無 markdown**：IG 不支援 **bold** 或其他格式
- **比 Threads 更視覺化**：IG 以圖為主，文案輔助圖片說故事
- **每平台重新生成**：IG 版不能直接複製 Threads 文案
- **無法點擊 URL**：IG 正文連結不可點，引導用 link-in-bio

---

## Fallback 處理

| 情境 | 處理 |
|---|---|
| 無圖片 | 告知使用者選項：(A) 提供圖片 URL (B) 跳過 IG (C) 改發 Threads |
| 圖片 URL 不公開 | 確認 URL 直接打開可看到圖片（非需登入頁面） |
| Container 狀態 ERROR | 重新建立 container，等待更長時間再 publish |
| Token 刷新失敗 | 需重新走 OAuth 流程取得新 token |
| 返回 null ID | Meta 暫時故障，稍後重試 |
