# API 整合指南

> 本文涵蓋 Instagram Graph API + Threads API 的 token 管理、刷新流程、故障排除。  
> **注意**: 舊的 Instagram Basic Display API 已廢棄，本指南不再涵蓋。

---

## 快速對照表

| 項目 | Instagram Graph API | Threads API |
|---|---|---|
| Host | `graph.instagram.com` | `graph.threads.net` |
| API Version | `v21.0` (可設定) | `v1.0` |
| Token 類型 | Instagram User Access Token | Threads User Access Token |
| Token 有效期 | **60 天**（可刷新） | **60 天**（可刷新） |
| 刷新端點 | `graph.instagram.com/refresh_access_token` | `graph.threads.net/refresh_access_token` |
| grant_type | `ig_refresh_token` | `th_refresh_token` |
| 發文端點 Step 1 | `/{user_id}/media` | `/{user_id}/threads` |
| 發文端點 Step 2 | `/{user_id}/media_publish` | `/{user_id}/threads_publish` |
| 發文格式 | 必須有圖片（IMAGE） | 純文字 OK（TEXT） |

---

## Token 刷新流程

### Instagram Token 刷新

Long-lived token 有效期 60 天，刷新後重置 60 天。**建議每 30 天刷新一次**。

```bash
# cURL 刷新
curl "https://graph.instagram.com/refresh_access_token\
?grant_type=ig_refresh_token\
&access_token=YOUR_CURRENT_TOKEN"

# 回應
{
  "access_token": "NEW_LONG_LIVED_TOKEN",
  "token_type": "bearer",
  "expires_in": 5183944
}
```

**Python 刷新（自動更新 config.json）：**

```python
from post_to_social import refresh_instagram_token
success = refresh_instagram_token("config.json")
```

或直接呼叫：

```python
import requests, json, time

def refresh_instagram_token(config_path="config.json"):
    with open(config_path) as f:
        config = json.load(f)

    token = config["instagram"]["access_token"]
    resp = requests.get(
        "https://graph.instagram.com/refresh_access_token",
        params={"grant_type": "ig_refresh_token", "access_token": token},
    )
    data = resp.json()
    config["instagram"]["access_token"] = data["access_token"]
    config["instagram"]["expires_at"] = int(time.time()) + data["expires_in"]

    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    return True
```

### Threads Token 刷新

```bash
# cURL 刷新
curl "https://graph.threads.net/refresh_access_token\
?grant_type=th_refresh_token\
&access_token=YOUR_CURRENT_TOKEN"

# 回應
{
  "access_token": "NEW_THREADS_TOKEN",
  "token_type": "bearer",
  "expires_in": 5183944
}
```

**Python 刷新（自動更新 config.json）：**

```python
from post_to_social import refresh_threads_token
success = refresh_threads_token("config.json")
```

**⚠️ 注意**:
- 刷新 Threads token 要用 `graph.threads.net`（舊文件可能寫 `graph.instagram.com`，已錯誤）
- grant_type 是 `th_refresh_token`，不是 `ig_refresh_token`

---

## 發文流程（P2 階段）

```
1. 讀 content_plan.md 確認今天公式 + 平台
2. 讀 style_profile.md 學語氣
3. 生成草稿（依 SKILL.md 規則）
4. 預覽 + 請使用者「確認」（安全閘，不可跳過）
5. 檢查 token 有效期（若 < 7 天 → 提醒刷新）
6. 呼叫 post_to_social.py:
   - Threads: manager.post_to_threads(text)
   - IG + Threads: manager.post_to_both(threads_text, ig_caption, image_url)
7. 更新 content_plan.md 戰績（記錄 post_id）
```

---

## config.json 結構

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
  },
  "threads": {
    "user_id": "27062622620054262",
    "app_id": "990908076790797",
    "app_secret": "YOUR_THREADS_APP_SECRET",
    "access_token": "THAAOFxxxx...",
    "token_type": "bearer",
    "expires_at": 1784604143
  },
  "token_refresh": {
    "auto_refresh": true,
    "refresh_before_expiry_minutes": 5
  }
}
```

---

## 首次設定（新 Instagram Graph API Token）

1. 去 [Meta App Dashboard](https://developers.facebook.com/) → App ID: 990908076790797
2. **新增產品** → Instagram → Business Login for Instagram
3. **Permissions** 加上：`instagram_business_basic`、`instagram_business_content_publish`
4. **OAuth Flow** 取得 short-lived token (1 小時)
5. **換 long-lived token** (60 天):
   ```bash
   curl "https://graph.instagram.com/access_token\
   ?grant_type=ig_exchange_token\
   &client_secret=APP_SECRET\
   &access_token=SHORT_LIVED_TOKEN"
   ```
6. **取得 Instagram User ID**:
   ```bash
   curl "https://graph.instagram.com/me?fields=id,username&access_token=TOKEN"
   # → { "id": "17841400000000000", "username": "your_ig_handle" }
   ```
7. **更新 config.json**:
   ```python
   from post_to_social import update_instagram_in_config
   update_instagram_in_config(
       user_id="17841400000000000",
       access_token="IGAAxxxx...",
   )
   ```

---

## 故障排除

### Token 相關

| 問題 | 原因 | 解決 |
|---|---|---|
| 401 Unauthorized | Token 過期 | 執行 token refresh |
| 400 Invalid Token | Token 格式錯誤 | 確認 token 完整複製（無空格） |
| Token 刷新失敗 | Token 已過 60 天完全失效 | 重新走 OAuth Flow |
| Threads 用 ig_refresh_token 失敗 | 端點/grant_type 錯誤 | 改用 `th_refresh_token` + `graph.threads.net` |

### Instagram 發文相關

| 問題 | 原因 | 解決 |
|---|---|---|
| 403 `#10` | 缺少 `instagram_business_content_publish` 權限 | 重新授權 |
| 400 圖片下載失敗 | image_url 需登入或已失效 | 確認 URL 公開可訪問 |
| Container status = ERROR | 圖片格式不對 | 確認是 JPEG，重試 |
| 帳號無法發文 | 帳號是個人帳號，非 Business/Creator | 轉換為專業帳號 |

### Threads 發文相關

| 問題 | 原因 | 解決 |
|---|---|---|
| 400 字數超限 | > 500 字 | 分串發（`post_thread(parts=[...])` |
| 403 Forbidden | user_id 與 token 不匹配 | 確認 config.json 的 user_id 與 token 對應同一帳號 |

---

## Token 安全規則

⚠️ **必須遵守**：

```
🔴 絕不提交 config.json 到 Git（已加入 .gitignore）
✅ 只提交 config.example.json（示意用，含佔位符）
✅ 環境變數 CONFIG_FILE_PATH 指向 config.json 路徑
✅ 若 token 意外暴露到聊天 → 立即告知使用者在 Meta Dashboard 重新核發
🔴 絕不在日誌 / 程式碼中印出完整 token
```

---

## 自動刷新建議

在 cron / 排程中每月刷新一次：

```bash
# 每月 1 日 00:00 刷新兩個平台 token
0 0 1 * * cd /path/to/project && python -c "
from post_to_social import refresh_instagram_token, refresh_threads_token
refresh_instagram_token('config.json')
refresh_threads_token('config.json')
print('Tokens refreshed')
"
```
