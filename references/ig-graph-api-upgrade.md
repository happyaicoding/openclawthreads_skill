# Instagram Graph API 升級指南

## 評估清單：我需要升級嗎？

| 檢查項目 | 未升級狀態 | 已升級狀態 |
|---|---|---|
| Meta App Dashboard 顯示 | 「Instagram Basic Display」 | 「Instagram Graph API」 |
| 發文能力 | ❌ 無法透過 API 發文 | ✅ 可發文、讀取洞察 |
| Token 類型 | Basic Display Token | Graph API Long-lived Token |
| 適用帳號 | 個人帳號 | Business / Creator 帳號 |

**若你只看到「Instagram Basic Display API」** → 需要升級，按下方步驟操作。

---

## 升級前提

- Instagram 帳號已轉換為 **Business** 或 **Creator** 帳號
  - Instagram app → 設定 → 帳號 → 轉換成專業帳號
  - 轉換後不影響已發佈內容
- 擁有 Facebook 粉絲頁（Instagram Business 帳號需連結 FB 粉絲頁）

---

## 步驟 1：建立 Meta App（若尚未建立）

1. 前往 [Meta for Developers](https://developers.facebook.com/)
2. 點選「我的應用程式」→「建立應用程式」
3. 選擇類型：**消費者（Consumer）**
4. 填入應用名稱、聯絡 Email
5. 記下 **App ID** 和 **App Secret**（填到 `config.json`）

---

## 步驟 2：在 App 加入 Instagram Graph API 產品

1. 進入 App Dashboard
2. 左側選單 → 「新增產品」
3. 找到 **Instagram Graph API** → 點「設定」
4. 按照引導連結你的 Instagram 帳號

---

## 步驟 3：設定 OAuth 權限

在 App Dashboard → App Review → 申請以下權限：

| 權限 | 用途 |
|---|---|
| `instagram_business_basic` | 讀取帳號資訊 |
| `instagram_business_content_publish` | 發文（必須）|
| `instagram_business_manage_messages` | 私訊管理（可選）|
| `instagram_business_manage_insights` | 查看洞察數據（可選）|
| `instagram_business_manage_comments` | 留言管理（可選）|

> 開發測試階段：可先在 App Dashboard 加入測試帳號，無需通過 App Review。

---

## 步驟 4：取得授權碼（Authorization Code）

引導使用者到以下 URL 授權：

```
https://www.instagram.com/oauth/authorize?
  client_id=YOUR_APP_ID
  &redirect_uri=YOUR_REDIRECT_URI
  &scope=instagram_business_basic,instagram_business_content_publish
  &response_type=code
```

- `YOUR_APP_ID`：從 App Dashboard 取得
- `YOUR_REDIRECT_URI`：你的回調 URL（開發時可用 `https://localhost:3000/callback`）
- 授權後 URL 中的 `code=XXXXXXX` 就是授權碼

---

## 步驟 5：用授權碼換取短期 Token

```bash
curl -X POST https://graph.instagram.com/v24.0/oauth/access_token \
  -d "client_id=YOUR_APP_ID" \
  -d "client_secret=YOUR_APP_SECRET" \
  -d "grant_type=authorization_code" \
  -d "redirect_uri=YOUR_REDIRECT_URI" \
  -d "code=AUTHORIZATION_CODE"
```

回應：
```json
{
  "access_token": "IGAABXzShortLived...",
  "token_type": "bearer"
}
```

---

## 步驟 6：將短期 Token 轉為長期 Token（60 天有效）

```bash
curl -X GET "https://graph.instagram.com/access_token" \
  -d "grant_type=ig_refresh_token" \
  -d "access_token=SHORT_LIVED_TOKEN"
```

回應：
```json
{
  "access_token": "IGAABXzLongLived...",
  "token_type": "bearer",
  "expires_in": 5183944
}
```

`expires_in` 是秒數。轉為 Unix timestamp：`int(time.time()) + 5183944`。

---

## 步驟 7：取得 Instagram User ID

```bash
curl "https://graph.instagram.com/v24.0/me?fields=id,username&access_token=LONG_LIVED_TOKEN"
```

回應：
```json
{
  "id": "17841400000000000",
  "username": "your_account"
}
```

---

## 步驟 8：更新 config.json

```json
{
  "instagram": {
    "user_id": "17841400000000000",
    "username": "your_account",
    "account_type": "BUSINESS",
    "app_id": "YOUR_APP_ID",
    "app_secret": "YOUR_APP_SECRET",
    "access_token": "IGAABXzLongLived...",
    "token_type": "bearer",
    "expires_at": 1234567890,
    "api_version": "v24.0",
    "host": "graph.instagram.com"
  }
}
```

---

## Threads 設定（同一 App）

Threads 使用相同的 Meta App 和 Token。額外需要：

1. 在 App Dashboard 加入 **Threads API** 產品
2. 申請 `threads_basic`、`threads_content_publish` 等權限
3. Threads User ID 通常與 Instagram User ID 不同（需單獨查詢）

查詢 Threads User ID：
```bash
curl "https://graph.threads.net/v1.0/me?fields=id,username&access_token=LONG_LIVED_TOKEN"
```

---

## 常見問題

**Q：「We couldn't find you on Instagram」**  
A：帳號未轉換為 Business/Creator 帳號。見「升級前提」。

**Q：`scope` 不被接受**  
A：確認使用新格式（`instagram_business_basic`，不是舊版的 `instagram_basic`）。

**Q：短期 Token 馬上過期**  
A：正常，短期 Token 僅有效 1 小時。務必執行步驟 6 轉為長期 Token。

**Q：長期 Token 刷新失敗（`invalid_token`）**  
A：Token 已完全過期（> 60 天沒刷新）。需重新從步驟 4 開始授權。

---

## 相關檔案

- `api-integration.md`：Token 刷新自動化
- `api-flow.md`：完整發文 API 流程
- `config.example.json`：config.json 填寫範本
