# social-post (OpenClaw API-only 版)

自動學習你的寫作風格（從本機 MD 文件）、規劃 14 天內容日曆、並自動發文到 **Instagram + Threads**（Graph API + Meta API）。

**版本：** 1.0.0-api (API-only，不依賴瀏覽器自動化)  
**原作者：** 駱君昊 (Hao)  
**源倉庫：** https://github.com/Hao0321/claude-skill-social-post

---

## 🚀 功能亮點

### 三階段工作流
- **P1 學風格** — 從本機 MD 資料夾讀取文章，AI 自動分析語氣特徵
- **P0 規劃日曆** — 依目標（擴大社群/轉換付費）規劃 14 天發文計劃
- **P2 每日發布** — 依日曆生成草稿、請你確認，自動發到 Instagram + Threads

### 實戰驗證爆款公式
- **F6b meta-ship** → 75K 觀眾、+1,319 Line 群成員
- **演算法復盤型** → 92.6% 非追蹤者、17K 瀏覽
- **社群 social proof** → 44K 觀眾、+1,239 入群
- **F19 Threads 立場宣言** → 26 萬瀏覽、76 轉發（Thread 原生公式）

### API-only 優勢
- ✅ **無瀏覽器依賴** — 不用 Stagehand / Chrome plugin，純 API 呼叫
- ✅ **穩定可靠** — 不受 DOM 變動影響，Meta 官方 API
- ✅ **自動 Token 管理** — 自動刷新 Access Token（60 天有效期）
- ✅ **跨平台一致** — 同一套 API 邏輯用於 IG + Threads
- ✅ **詳細錯誤處理** — 完整故障排除與日誌記錄

### 核心規則
- **R1** — 一天最多 1 篇，不跳過任何一天
- **R5** — 同敘事意圖 4 天內不重複、月最多 2 次
- **R25** — Threads 正文絕不附外部連結（用留言 CTA 替代）
- **R6** — 48-72h 後才評估成敗（早期數據會 underestimate 60-80%）

---

## 📋 前置需求

### 必須
- OpenClaw 已安裝
- **Instagram Graph API** 已升級（見下方「API 升級指南」）
  - 不是「Basic Display API」
  - 需要 Long-lived Access Token + Refresh Token
- **Threads Meta API** 可用（綁定同一 Meta 應用）
- `config.json` 已設定，包含有效的 API credentials

### 不需要
- ❌ Chrome plugin / Stagehand
- ❌ 瀏覽器自動化
- ❌ 手動登入各平台

---

## 🔧 安裝

### Step 1：準備 Instagram Graph API

若你的帳號還在「Basic Display API」，需要升級。

```bash
# 檢查清單見 references/ig-graph-api-upgrade.md
# 簡單版本：
# 1. 在 Meta App Dashboard 升級應用到 Graph API
# 2. 取得長期 Access Token（60 天有效）
# 3. 取得 Refresh Token（用於自動更新）
# 4. 確認 Threads 帳號已啟用
```

詳細步驟見下方「API 升級指南」。

### Step 2：設定 config.json

```bash
# 複製範本
cp config.example.json config.json

# 編輯 config.json，填入你的認證信息
{
  "instagram": {
    "user_id": "17841400000000",        # Instagram Business Account ID
    "app_id": "123456789",
    "app_secret": "abc123def456xyz...",
    "access_token": "IGAABXz...",       # Long-lived Access Token
    "token_type": "bearer",
    "expires_at": 1234567890            # Unix timestamp
  },
  "threads": {
    "user_id": "123456789",             # Threads User ID
    "app_id": "123456789",              # 同 Instagram app
    "app_secret": "abc123def456xyz...", # 同 Instagram
    "access_token": "IGAABXz...",       # 同 Instagram token
    "token_type": "bearer",
    "expires_at": 1234567890
  },
  "token_refresh": {
    "auto_refresh": true,
    "refresh_before_expiry_minutes": 5  # Token < 5 分鐘過期時自動更新
  }
}
```

**重要：** `config.json` 已在 `.gitignore` 中，**不會上傳 Git**。

### Step 2.5：安裝 Python 依賴

```bash
pip install -r requirements.txt
# 或單獨安裝：
pip install requests
```

### Step 3：安裝 OpenClaw Skill

```bash
# 重新命名目錄（GitHub 解壓後名稱不同）
# 下載 zip 解壓後目錄叫 openclawthreads_skill-main，需改名為 social-post
mv openclawthreads_skill-main social-post

# 複製到 OpenClaw skills 目錄
cp -r social-post ~/.openclaw/workspace/skills/social-post

# 重啟 OpenClaw gateway（或新開 session）
```

確認安裝：
```bash
ls ~/.openclaw/workspace/skills/social-post/SKILL.md
```

### Step 4：設定環境變數

OpenClaw 發文時需要知道 `config.json` 位置：

```bash
export CONFIG_FILE_PATH="/absolute/path/to/config.json"
```

或在 OpenClaw 啟動前設定：
```bash
source ~/.openclaw/setup.sh
# 添加上面的 export 到該檔案
```

---

## 🎯 使用方式

### 觸發詞（任一即可）

在 OpenClaw chat 裡說：

| 意圖 | 範例 |
|---|---|
| **學風格** | 「幫我學寫作風格」「分析我的語氣」「重新學風格」「讀 MD 資料夾」 |
| **規劃日曆** | 「幫我排社群內容日曆」「重新規劃 14 天」「排新的內容」 |
| **發文** | 「今天發一篇」「發文」「PO 一下」「發到 IG 和 Threads」 |
| **查成績** | 「這篇怎麼樣」「查一下流量」「分析今天的貼文」 |

### 典型對話流程

#### 初次設定（P1 + P0）
```
你：「幫我從 MD 資料夾學風格」
→ OpenClaw：「請提供 MD 資料夾的完整路徑」
你：「/home/user/posts 或 C:\Users\...\posts」
→ OpenClaw：[讀取 10+ 篇 MD、分析語氣、生成 style_profile.md]
✓ 語氣 profile 已生成

你：「幫我規劃 14 天日曆」
→ OpenClaw：「目標是什麼？擴大社群還是轉換付費？」
你：「擴大 IG 社群，每天一篇」
→ OpenClaw：[按 19 個公式、平衡節奏、生成 content_plan.md]
✓ 14 天日曆已規劃
```

#### 每日發文（P2）
```
你：「今天發一篇」
→ OpenClaw：「今天是 Day 3，要講什麼嗎？」
你：「我今天用 Claude 寫了個工具」
→ OpenClaw：[讀日曆、讀 style_profile、生成 2 個平台草稿]
✓ 草稿已生成
IG: [圖文內容]
Threads: [口語版本]
「確認發到 Instagram + Threads 嗎？」
你：「確認」
→ OpenClaw：[呼叫 API 發文]
✓ 已發到 Instagram（連結：...）
✓ 已發到 Threads（連結：...）
```

#### 成績分析（診斷）
```
你：「查一下數據」
→ OpenClaw：「貼一下貼文的觀看數 / 讚 / 留言 / 分享」
你：「IG 247 讚、12 留言」
→ OpenClaw：[按 4 指標評估]
「這篇互動率 4.8%，追蹤者觸及 65%，算 deep-conversion 型...」
```

---

## 🔐 API 升級指南（Instagram Graph API）

### 目前狀況檢查

```bash
# 見 references/ig-graph-api-upgrade.md 的「評估清單」
# 或簡單版本：

# ✅ 如果你能在 Meta App Dashboard 看到 Graph API permissions
# → 已升級，直接進到「取得 Token」

# ❌ 如果你只看到「Instagram Basic Display」
# → 需要升級到「Instagram Graph API」
```

### OAuth 授權流程

1. **建立 Meta 應用**（若尚未建立）
   - 到 https://developers.facebook.com/
   - 建立新應用 → 選「消費者」類型

2. **升級到 Graph API**
   - 在 App Dashboard 添加「Instagram Graph API」產品
   - 要求審核 `instagram_basic` + `instagram_content_publish` 權限

3. **開始 OAuth 流程**
   - 引導使用者到：
   ```
   https://www.instagram.com/oauth/authorize?
     client_id=YOUR_APP_ID
     &redirect_uri=YOUR_REDIRECT_URI
     &scope=instagram_business_profile,instagram_content_publish
     &response_type=code
   ```

4. **交換短期 Token**
   ```bash
   curl -X POST https://graph.instagram.com/v18.0/oauth/access_token \
     -d "client_id=YOUR_APP_ID" \
     -d "client_secret=YOUR_APP_SECRET" \
     -d "grant_type=authorization_code" \
     -d "redirect_uri=YOUR_REDIRECT_URI" \
     -d "code=AUTHORIZATION_CODE"
   ```

5. **轉換為長期 Token**
   ```bash
   curl -X GET https://graph.instagram.com/access_token \
     -d "grant_type=ig_refresh_token" \
     -d "access_token=SHORT_LIVED_TOKEN"
   ```

6. **更新 config.json**
   - 填入 `instagram.access_token`（長期）
   - 填入 `instagram.expires_at`（Unix timestamp）

詳見 `references/ig-graph-api-upgrade.md`。

---

## 📚 核心概念

### 敘事意圖（R5）
「主題」不是公式，而是**敘事意圖**：
- `promo` — 產品 ship（Day 1: 75K 觀眾）
- `演算法復盤` — 數據分析（Day 6: 17K 觀眾）
- `社群 social proof` — pitch 群價值（5/5: 44K 觀眾）
- `教學型`、`合作達成`、`預告`、`反思` 等

**月配額 = 敘事意圖數，不是公式總數**。每個意圖可月發 2 次、4 天內不重複。

### Viral 4 條件（必須 AND）
```
Viral = 4 段 4 句結構
      + 純血 voice（跟 style_profile 一致）
      + 全新敘事意圖（4 天冷卻、月配額）
      + 黃金時段（22:00-01:00）
```

缺一條 → flop。Day 5 同敘事意圖距 4 天 → 觸及只有 0.13%。

### 真 KPI（R7）
不是讚數，而是**社群轉化**：
- IG / Threads 粉絲成長
- GitHub star
- 付費學員

Day 1 實證：380 讚 → +1,319 Line 群。早期數據會低估 60-80%，要等 48-72h plateau。

### Threads 獨特公式（F19）
Threads 不適合 F6b（FB 爆款公式），需用**F19 立場宣言型**：
- 1 段不換行
- 60-150 字
- 熱門 keyword + 對立敘事
- 無 CTA 無連結

實證：hao0321_studio 400 粉 → 10K 粉 / 7 天（3 篇 F19）。

---

## 🛡️ 安全規則

### 發文前必須確認
**每次發佈前，OpenClaw 會問「確認發到 IG / Threads 嗎？」— 你一定要回「確認」才會發。** 沒有確認字眼就不發。

### API 密鑰保護
- ✅ `config.json` 在 `.gitignore`，不會上傳 Git
- ✅ Token 只從 `config.json` 讀取，不硬編碼
- ❌ 不要在聊天中貼出真實 token
- ❌ 若 token 意外暴露，立即在 Meta App Dashboard 重新核發

### 不要做的事
- ❌ 沒授權發文就發
- ❌ 跨平台複製同一段文（IG 視覺化、Threads 口語短句）
- ❌ 自動按讚 / 回覆 / 大量留言
- ❌ 外傳 `config.json`（含 token）或 `style_profile.md`（個人語氣）
- ❌ 刪除使用者留言 / 貼文

---

## 🔧 故障排除

### Token 過期（401 Unauthorized）
```
❌ 錯誤：401 Unauthorized

✅ 解法：
1. 檢查 config.json 的 expires_at（是否已過期）
2. OpenClaw 會自動刷新（見 token_refresh.auto_refresh）
3. 若自動更新失敗 → 重新授權（見上方「API 升級指南」）
```

### Instagram 發文失敗（圖片問題）
```
❌ 錯誤：400 Bad Request / 403 Forbidden

✅ 檢查清單：
- 圖片格式是否正確？（JPG / PNG / GIF，不支援 HEIC）
- 圖片大小 < 10 MB？
- 帳號是否已升級到 Graph API？
- 應用是否有 instagram_content_publish 權限？
```

### Threads 分串失敗
```
❌ 錯誤：發到一半整串遺失

✅ 預防：
- 發分串前逐則預覽確認
- 字數檢查（每則 < 500 字）
- 句子邊界切割（不要無謂斷句）
```

### 速率限制（429 Too Many Requests）
```
❌ 錯誤：429 Too Many Requests

✅ 解法：
- Instagram：發完後等至少 30 秒再發下一篇
- Threads：發完後等至少 10 秒再發下一篇
- 分串 Threads：每則間 2-3 秒
```

### config.json 路徑問題
```
❌ 錯誤：找不到 config.json

✅ 檢查清單：
- CONFIG_FILE_PATH 環境變數是否設定？
- 路徑是否是絕對路徑？（不能是相對路徑）
- 檔案是否真的存在？
- 有無讀取權限？
```

---

## 📁 檔案結構

```
social-post/                          # 安裝後目錄名稱
├── SKILL.md                          # Skill 主邏輯（OpenClaw 1.0.0-api）
├── post_to_social.py                 # IG + Threads 雙平台發文腳本
├── refresh_token.py                  # Token 手動刷新工具
├── requirements.txt                  # Python 依賴（requests）
├── config.example.json               # API credentials 填寫範本
├── config.json                       # 你的 API credentials（gitignored）
├── style_profile.example.md          # 語氣 profile 範本
├── content_plan.example.md           # 14 天日曆範本
├── futureplan.md                     # 功能開發路線圖
├── .gitignore                        # 保護 config.json、style_profile.md 等
└── references/
    ├── learn_style.md                # P1：從 MD 資料夾學風格
    ├── phase0_plan.md                # P0：規劃 14 天日曆
    ├── generate_and_publish.md       # P2：生成 + 發佈（API 版）
    ├── api-flow.md                   # 完整 API 發文流程
    ├── api-integration.md            # Token 刷新 + 故障排除
    ├── ig-graph-api-upgrade.md       # Instagram Graph API 升級指南
    ├── instagram.md                  # IG 發文（API 版本）
    ├── threads.md                    # Threads 發文（Meta API 版本）
    ├── formulas.md                   # 19 個 viral 公式（F1-F19）
    ├── evaluation.md                 # 4 指標評估框架
    └── case_studies.md               # Day 1-4 實戰案例解剖
```

---

## 📊 版本歷史

### v1.0.0-api（API-only 首版）✨
- 🚀 **完全移除瀏覽器依賴** — 從 Stagehand 轉為純 API
- 📱 **僅支援 Instagram + Threads** — 移除 Facebook 和 X
- 🔑 **API 認證管理** — config.json + 自動 token 刷新
- 🔐 **增強安全** — 密鑰保護、credential 隔離
- 📚 **新文件** — `api-flow.md` / `api-integration.md`
- 🎯 **MD 資料夾學風格** — 動態路徑輸入（v0.9 已有，v1.0 更成熟）

### v0.9.0（OpenClaw Stagehand 版）
- 🔄 從 Claude Code 轉換到 OpenClaw
- 🌐 Stagehand 瀏覽器自動化
- 📁 **新功能：Option B 從 MD 資料夾學風格**
- 🔧 所有平台發文指令更新為 `browser navigate/act/extract`

### v0.8.6（Claude Code 最後一版）
- F19 Threads 立場宣言型公式
- R19 Thread 轉發權重 + keyword 機制
- R15-R18 私訊分享、長留言、Reels、儲存指標

詳見原倉庫 `CHANGELOG.md`。

---

## ❓ 常見問題

**Q：Instagram 和 Threads 可以用同一個 token 嗎？**  
A：可以。Threads 是 Meta 旗下（Facebook 公司），與 Instagram 共享同一 OAuth 認證系統。

**Q：支援多帳號嗎？**  
A：支援，但 token 綁定特定帳號。多帳號時需切換 config.json 中的 token（或寫腳本動態切換）。

**Q：可以改公式嗎？**  
A：可以！改 `formulas.md` 或 `style_profile.md`。改完自動生效。

**Q：成績怎麼追蹤？**  
A：每發完一篇，自動寫進 `content_plan.md` 戰績表。兩週 review 時讓 OpenClaw 幫你分析表現最好 / 最差的公式。

**Q：用 MD 資料夾學風格，支援哪些語言？**  
A：任何語言都行。OpenClaw 萃取的是**句式、標點、emoji、開頭收尾習慣**，這些超越語言。

**Q：為什麼不支援 Facebook 和 X 了？**  
A：API-only 版本優先穩定和安全。Facebook 和 X 的 API 變動頻繁、核准流程複雜，v1.0 先聚焦 IG + Threads（Meta 官方 API 最穩定）。未來可能重新加回。

---

## 📞 授權 & 致謝

[MIT License](../LICENSE) — 隨便改、隨便用、商用也行。

**原作者：** 駱君昊 (Hao)  
**Facebook：** https://www.facebook.com/lo.jain.hao  
**社群：** [Claude Code 台灣交流討論區](https://line.me/ti/g2/DPTQR_XE6IYP8c5lBxsbRwsvEUsxI-70p1jWoA)

---

## 🎯 下一步

1. ✅ 升級 Instagram 到 Graph API（見上方「API 升級指南」）
2. ✅ 準備 `config.json`（複製 `config.example.json` 並填入 token）
3. ✅ 設定 `CONFIG_FILE_PATH` 環境變數
4. ✅ 安裝 OpenClaw skill（見上方「安裝」）
5. 📚 在 OpenClaw 對話裡說「幫我從 MD 資料夾學風格」
6. 🎯 完成 P1（學風格）+ P0（規劃日曆）設定
7. 📱 每天「今天發一篇」，享受自動發文

---

**問題或建議？** 回報 issue：https://github.com/Hao0321/claude-skill-social-post/issues  
**需要幫助？** 提問 PR 或討論區：[Claude Code 台灣](https://line.me/ti/g2/DPTQR_XE6IYP8c5lBxsbRwsvEUsxI-70p1jWoA)
