# Future Plan -- 長期開發建議與權限確認

> 最後更新：2026-05-23
> 基於 post_to_social.py v1.0 code review 後的改進方向

---

## 目前已完成

| 項目 | 狀態 | 說明 |
|---|---|---|
| Threads API 發文 | Done | ThreadsAPI class, TEXT + IMAGE + VIDEO |
| Instagram Graph API 發文 | Done | InstagramAPI class, IMAGE 單張 |
| 雙平台同步發文 | Done | SocialPostManager.post_to_both() |
| Token 自動刷新 | Done | refresh_instagram_token() / refresh_threads_token() |
| config.json BOM 相容 | Done | utf-8-sig encoding |
| Windows CP950 相容 | Done | 全 ASCII 輸出，無 Unicode 符號 |

---

## 建議功能開發

### #1 錯誤重試機制 (Retry with Backoff)

**優先級**：高
**難度**：低
**需要權限**：無（純邏輯）

目前 API 呼叫失敗即停止。建議加入指數退避重試：
- 5xx Server Error：最多重試 3 次，間隔 2s / 4s / 8s
- 429 Rate Limit：讀取 Retry-After header，等待後重試
- 4xx Client Error：不重試，直接報錯

**實作位置**：`SocialMediaAPI` base class 加 `_request_with_retry()` method

---

### #2 結構化日誌 (Structured Logging)

**優先級**：中
**難度**：低
**需要權限**：無（純邏輯）

目前用 print() 輸出。建議改用 Python logging module：
- 支援 DEBUG / INFO / WARNING / ERROR 等級
- 可輸出到檔案（發文紀錄）
- 不影響現有 print 行為（加 StreamHandler）

**注意**：日誌中絕不可出現 access_token（安全規則）

---

### #3 發文紀錄持久化 (Post History)

**優先級**：中
**難度**：中
**需要權限**：無（本地檔案）

每次成功發文後，自動記錄到 `post_history.json`：
```json
{
  "posts": [
    {
      "timestamp": "2026-05-23T22:00:00",
      "platform": "instagram",
      "media_id": "18117891727666330",
      "caption_preview": "欠債 180 萬的時候...",
      "image_url": "https://cdn.midjourney.com/...",
      "status": "success"
    }
  ]
}
```
用途：戰績追蹤、R5 敘事意圖冷卻檢查、防重複發文

---

### #4 Dry-Run 模式 (Preview without Posting)

**優先級**：中
**難度**：低
**需要權限**：無（純邏輯）

加入 `--dry-run` 參數或 `dry_run=True`：
- 驗證 config.json 設定
- 檢查 token 有效性
- 印出將要發送的 API 請求內容
- 不實際呼叫 POST 端點

**實作方式**：在 `post()` method 加 `dry_run` 參數

---

### #5 命令列介面 (CLI with argparse)

**優先級**：低
**難度**：中
**需要權限**：無（純邏輯）

目前發文需要改 main() 中的變數。建議加 CLI：
```bash
python post_to_social.py --mode dual \
  --threads-text "你的 Threads 文字" \
  --ig-caption "你的 IG 文字" \
  --image-url "https://..." \
  --config config.json
```
或從檔案讀取：
```bash
python post_to_social.py --mode dual --content draft.json
```

---

### #6 Token 到期自動提醒

**優先級**：高
**難度**：低
**需要權限**：無需額外 API 權限

Token 刷新使用的端點：
- Instagram: `GET /refresh_access_token?grant_type=ig_refresh_token`
- Threads: `GET /refresh_access_token?grant_type=th_refresh_token`

**只需要持有有效的 long-lived token 即可刷新，不需要任何額外權限。**

目前 `post_to_social.py` 已實作自動刷新邏輯，建議額外加入：
- 每次執行時檢查距到期天數
- < 7 天：自動刷新 + 更新 config.json
- < 30 天：印出提醒
- 已過期：停止發文 + 提示重新走 OAuth

**權限確認**：
| 權限 | 需要 | 目前狀態 |
|---|---|---|
| 有效 long-lived token | 是 | 已有 |
| 額外 scope | 否 | 不需要 |

---

### #7 Carousel 輪播貼文 (Instagram)

**優先級**：中
**難度**：中
**需要權限**：`instagram_business_content_publish` (已有)

Instagram Carousel 使用同一個 `POST /{user_id}/media` 端點，流程：

1. **為每張圖片建立子容器**：
   ```
   POST /{user_id}/media
   ?image_url={url}&is_carousel_item=true&access_token={token}
   ```
   回傳子容器 ID

2. **建立 Carousel 容器**：
   ```
   POST /{user_id}/media
   ?media_type=CAROUSEL&caption={text}&children={id1,id2,...}&access_token={token}
   ```

3. **發布 Carousel**：
   ```
   POST /{user_id}/media_publish
   ?creation_id={carousel_container_id}&access_token={token}
   ```

**限制**：
- 每個 Carousel 最多 10 張圖片/影片
- 圖片比例必須一致（建議 1:1 或 4:5）
- 混合圖片+影片也可以

**權限確認**：
| 權限 | 需要 | 目前狀態 |
|---|---|---|
| `instagram_business_content_publish` | 是 | 已有 |
| `instagram_business_basic` | 是 | 已有 |
| 額外 scope | 否 | 不需要 |

**實作位置**：`InstagramAPI` class 加 `post_carousel()` method

---

### #8 Reels 短影片 (Instagram)

**優先級**：低（目前以圖片+文字為主）
**難度**：高
**需要權限**：`instagram_business_content_publish` (已有，但上傳方式有限制)

Reels 使用同一個 `POST /{user_id}/media` 端點：
```
POST /{user_id}/media
?media_type=REELS&video_url={url}&caption={text}&access_token={token}
```

**上傳方式限制（重要）**：

| 上傳方式 | Instagram Login (目前使用) | Facebook Login for Business |
|---|---|---|
| `video_url`（公開 URL） | 可用 | 可用 |
| Resumable Upload (`rupload.facebook.com`) | 不可用 | 可用 |

目前使用 **Instagram Login**，因此：
- 影片必須先上傳到可公開存取的伺服器（如 CDN、S3、Cloudflare R2）
- 再將公開 URL 傳給 `video_url` 參數
- **無法**使用 `rupload.facebook.com` 的斷點續傳功能

**影片規格**：
- 格式：MP4（H.264 編碼、AAC 音訊）
- 長度：3 秒 ~ 15 分鐘
- 比例：9:16（直式）建議
- 最大檔案：1 GB

**權限確認**：
| 權限 | 需要 | 目前狀態 |
|---|---|---|
| `instagram_business_content_publish` | 是 | 已有 |
| `instagram_business_basic` | 是 | 已有 |
| Resumable Upload | 需 Facebook Login for Business | 目前用 Instagram Login，不可用 |
| `video_url` 方式 | 無額外權限 | 可用 |

**實作位置**：`InstagramAPI` class 加 `post_reel()` method

---

## 權限總覽

### 目前持有的權限

**Instagram** (`graph.instagram.com` v24.0)：
- `instagram_business_basic`
- `instagram_business_content_publish`
- `instagram_business_manage_messages`
- `instagram_business_manage_insights`
- `instagram_business_manage_comments`

**Threads** (`graph.threads.net` v1.0)：
- `threads_basic`
- `threads_content_publish`
- `threads_manage_replies`
- `threads_manage_insights`
- `threads_read_replies`

### 各功能所需權限對照

| 功能 | 所需權限 | 目前狀態 | 備註 |
|---|---|---|---|
| 單張圖片發文 (IG) | `instagram_business_content_publish` | 已有 | 已實作 |
| 文字/圖片/影片發文 (Threads) | `threads_content_publish` | 已有 | 已實作 |
| Token 刷新 | 無需額外權限 | 可用 | 只需有效 long-lived token |
| Carousel 輪播 (IG) | `instagram_business_content_publish` | 已有 | 待開發 |
| Reels 短影片 (IG) | `instagram_business_content_publish` | 已有 | 待開發，限 video_url 方式 |
| 互動數據查詢 (IG) | `instagram_business_manage_insights` | 已有 | 可用於戰績追蹤 |
| 留言管理 (IG) | `instagram_business_manage_comments` | 已有 | 可用於自動回覆 |
| 私訊管理 (IG) | `instagram_business_manage_messages` | 已有 | 可用於 CTA 私訊 |
| 回覆管理 (Threads) | `threads_manage_replies` | 已有 | 可用於留言互動 |
| 互動數據查詢 (Threads) | `threads_manage_insights` | 已有 | 可用於戰績追蹤 |

### 目前不可用的功能

| 功能 | 原因 | 解決方案 |
|---|---|---|
| Resumable Upload (影片斷點續傳) | 需 Facebook Login for Business | 改用 video_url 或遷移到 FB Login |
| Facebook 粉絲頁發文 | 本專案不支援 FB | 不在範圍內 |

---

## 開發優先順序建議

### Phase 1（近期，1-2 週）
1. **#1 錯誤重試機制** -- 提高發文成功率，低開發成本
2. **#6 Token 到期自動提醒** -- 已部分實作，強化提醒邏輯

### Phase 2（中期，1 個月內）
3. **#3 發文紀錄持久化** -- 支援 SKILL.md R5 敘事意圖冷卻追蹤
4. **#4 Dry-Run 模式** -- 安全測試，避免誤發
5. **#7 Carousel 輪播** -- 豐富 IG 內容形式

### Phase 3（長期，按需開發）
6. **#2 結構化日誌** -- 改善除錯體驗
7. **#5 CLI 介面** -- 提升操作便利性
8. **#8 Reels 短影片** -- 配合 R17 Reels 策略

---

## 注意事項

- `config.json` 包含真實 token 和 app_secret，**絕不可** commit 到 git
- 所有日誌和輸出中**禁止**出現 access_token
- Token 有效期 60 天，建議每月 1 日主動刷新
- 目前使用 Instagram Login，若需 Resumable Upload 需遷移到 Facebook Login for Business
