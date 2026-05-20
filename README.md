# social-post (OpenClaw 版)

自動學習你的 Facebook 語氣風格、規劃 14 天內容日曆、並自動發文到 FB / Instagram / Threads / X。

**版本：** 0.9.0 (OpenClaw + Stagehand)  
**原作者：** 駱君昊 (Hao)  
**源倉庫：** https://github.com/Hao0321/claude-skill-social-post

---

## 功能亮點

### 三階段工作流
- **P1 學風格** — 支援兩種方式：
  - 🔵 **爬取 Facebook 個人頁** — AI 自動讀取你的 20+ 篇貼文，萃取語氣特徵
  - 🟢 **讀本機 MD 資料夾** — 提供資料夾路徑，AI 從你的寫作素材學風格（*新功能*）
- **P0 規劃日曆** — 依目標（擴大社群/轉換付費）規劃 14 天發文計劃
- **P2 每日發布** — 依日曆生成草稿、請你確認，自動發到四大平台

### 實戰驗證爆款公式
- **F6b meta-ship** → 75K 觀眾、+1,319 Line 群成員
- **演算法復盤型** → 92.6% 非追蹤者、17K 瀏覽
- **社群 social proof** → 44K 觀眾、+1,239 入群

### 核心規則
- **R1** — 一天最多 1 篇，不跳過任何一天
- **R5** — 同敘事意圖 4 天內不重複、月最多 2 次
- **R25** — FB/Threads 正文絕不附外部連結（用留言 CTA 替代）
- **R6** — 48-72h 後才評估成敗（早期數據會 underestimate 60-80%）

---

## 安裝

### 需求
- OpenClaw 已安裝
- **browser-automation skill** 已安裝（OpenClaw browser plugin）
- Chrome 已登入你要發文的社群帳號（FB、IG、Threads、X）

### 步驟

```bash
# 1. 複製到 OpenClaw skills 目錄
cp -r openclaw-social-post ~/.openclaw/workspace/skills/social-post

# 2. 重啟 OpenClaw gateway（或新開 session 讓 skill 自動載入）
```

確認安裝：
```bash
ls ~/.openclaw/workspace/skills/social-post/SKILL.md
# 應該看到檔案存在
```

---

## 使用方式

### 觸發詞（任一即可）
在 OpenClaw chat 裡說：

| 意圖 | 範例 |
|---|---|
| **學風格** | 「幫我學 FB 風格」「分析我的貼文語氣」「重新學風格」「讀 MD 資料夾」 |
| **規劃日曆** | 「幫我排社群內容日曆」「重新規劃 14 天」「排新的內容」 |
| **發文** | 「今天發一篇」「發文」「PO 一下」「現在發到 FB」 |
| **查成績** | 「這篇怎麼樣」「查一下流量」「分析今天的貼文」 |

### 典型對話流程

#### 初次設定（P1 + P0）
```
你：「幫我學 FB 風格」
→ OpenClaw：「要從 FB 爬取還是讀本機 MD 資料夾？」
你：「讀 MD 資料夾」
→ OpenClaw：「請提供資料夾路徑」
你：「/home/user/posts 或 C:\Users\...\posts」
→ OpenClaw：[讀取、分析、生成 style_profile.md]

你：「幫我排社群內容日曆」
→ OpenClaw：「目標是什麼？頻率？」
你：「擴大社群，每天一篇」
→ OpenClaw：[生成 14 天日曆到 content_plan.md]
```

#### 每日發文（P2）
```
你：「今天發一篇」
→ OpenClaw：「今天要講什麼？」
你：「我今天用 Claude 做了新功能」
→ OpenClaw：[讀日曆、生成 4 個平台草稿]
「確認發到 FB / Instagram / Threads / X 嗎？」
你：「確認」
→ OpenClaw：[自動發文] ✓ 已發到 FB...
```

#### 成績分析（診斷）
```
你：「查一下數據」
→ OpenClaw：「貼貼文的 insights 截圖或數字」
你：[貼圖]
→ OpenClaw：[按 4 指標評估] 「這篇是 deep conversion 型，ROI 在社群入群...」
```

---

## 新功能：Option B — 從 MD 資料夾學風格

**為什麼？** FB 個人頁不總是有 20+ 公開貼文，或你想用寫作素材（部落格、筆記）當風格樣本。

**怎麼用？**

1. **準備 MD 資料夾**
   ```
   ~/my-posts/
   ├── post-001.md
   ├── post-002.md
   ├── essay.md
   └── notes.md
   ```

2. **告訴 OpenClaw**
   ```
   你：「幫我從 MD 資料夾學風格」
   → OpenClaw：「請提供資料夾路徑」
   你：「/home/user/my-posts」（或 Windows: C:\Users\...\posts）
   ```

3. **AI 自動：**
   - 列出資料夾內所有 `.md` 檔
   - 讀取每個檔案，過濾掉 frontmatter / 標題 / code block
   - 只保留**正文段落**作為語氣樣本
   - 生成 `style_profile.md`，並在檔首記錄來源

**特色：**
- ✅ 路徑完全動態，不寫死（在任何機器都能用）
- ✅ 自動過濾 Markdown 結構（frontmatter、代碼塊不會污染分析）
- ✅ 支援 Windows / macOS / Linux 路徑格式
- ✅ 無需網路爬蟲，本地即時讀取

---

## 核心概念

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
- Line 群成長
- GitHub star
- 付費學員

Day 1 實證：380 讚 → +1,319 Line 群。早期數據會低估 60-80%，要等 48-72h plateau。

---

## 重要安全規則 🛡️

### 發文前必須確認
**每次發佈前，OpenClaw 會問「確認發到 X / Y / Z 嗎？」— 你一定要回「確認」才會發。** 沒有確認字眼就不發。

### 不要做的事
- ❌ 沒授權發文就發
- ❌ 跨平台複製同一段文（每平台重新生成）
- ❌ 自動按讚 / 回覆 / 大量留言
- ❌ 外傳 `style_profile.md`（個人語氣檔）
- ❌ 猜測 FB 網址（P1 必須問）
- ❌ 刪除使用者留言 / 貼文

---

## 故障排除

### browser-automation 斷線
```
❌ 錯誤：browser navigate / act / extract 失敗

✅ 解法：
1. 立即重試 2-3 次（通常幾秒自動恢復）
2. 若仍失敗 → 重啟 OpenClaw 或 browser plugin
3. 若還是不行 → 提供純文字草稿，由你手動發文
```

### FB DOM 選擇器失效
```
❌ 錯誤：找不到「在想些什麼」輸入框

✅ 解法：
OpenClaw 自動改用 browser extract "all text content" fallback
若還是失敗 → FB 可能改版，回報 issue
```

### 路徑問題（MD 資料夾選項）
```
❌ 錯誤：「資料夾不存在」或「沒有 .md 檔」

✅ 檢查清單：
- 路徑是否完整？（如 C:\Users\admin\posts 不能寫 \posts）
- 資料夾內是否真的有 .md 檔？
- Windows 用反斜線 \ 或正斜線 / 都行
- macOS / Linux 用正斜線 /
```

---

## 檔案結構

```
openclaw-social-post/
├── SKILL.md                          # Skill 主邏輯（OpenClaw frontmatter）
├── style_profile.example.md          # 語氣 profile 範本
├── content_plan.example.md           # 14 天日曆範本
└── references/
    ├── learn_style.md                # P1：學風格（FB + MD 資料夾）
    ├── phase0_plan.md                # P0：規劃日曆
    ├── generate_and_publish.md       # P2：生成 + 發佈
    ├── facebook.md                   # FB 發文 UI 流程
    ├── threads.md                    # Threads 發文 + 演算法指南
    ├── instagram.md                  # IG 發文
    ├── x.md                          # X/Twitter 發文
    ├── formulas.md                   # 13 個 viral 公式（F1-F19）
    ├── evaluation.md                 # 4 指標評估框架
    └── case_studies.md               # Day 1-4 實戰案例解剖
```

---

## 版本歷史

### v0.9.0（OpenClaw 首版）
- 🔄 從 Claude Code 轉換到 OpenClaw
- 🌐 Stagehand 瀏覽器自動化（替代 Chrome MCP）
- 📁 **新功能：Option B 從 MD 資料夾學風格**（路徑動態提供）
- 🔧 所有平台發文指令更新為 `browser navigate/act/extract/screenshot`

### v0.8.6（Claude Code 最後一版）
- F19 Threads 立場宣言型公式
- R19 Thread 轉發權重 + keyword 機制
- R15-R18 私訊分享、長留言、Reels、儲存指標

詳見 `CHANGELOG.md`（原倉庫）。

---

## 常見問題

**Q：會不會被 FB 當機器人封？**  
A：不會。skill 只是幫你填表單、按按鈕，速度跟你手動一樣。但不要連發很多篇（skill 本身有 24h 爆款冷卻規則）。

**Q：支援多帳號嗎？**  
A：支援，但要在 Chrome 裡提前登入對應帳號。Threads 桌面版沒帳號切換（只能手機切）。

**Q：可以改公式嗎？**  
A：可以！改 `formulas.md` 或 `style_profile.md`。改完自動生效。

**Q：成績怎麼追蹤？**  
A：每發完一篇，自動寫進 `content_plan.md` 戰績表。兩週 review 時讓 skill 幫你分析表現最好 / 最差的公式。

**Q：用 MD 資料夾學風格，支援哪些語言？**  
A：任何語言都行。skill 萃取的是**句式、標點、emoji、開頭收尾習慣**，這些超越語言。

---

## 授權 & 致謝

[MIT License](../LICENSE) — 隨便改、隨便用、商用也行。

**原作者：** 駱君昊 (Hao)  
**Facebook：** https://www.facebook.com/lo.jain.hao  
**社群：** [Claude Code 台灣交流討論區](https://line.me/ti/g2/DPTQR_XE6IYP8c5lBxsbRwsvEUsxI-70p1jWoA)

---

## 下一步

1. ✅ 安裝 skill（見上方「安裝」段）
2. 📚 在 OpenClaw 對話裡說「幫我學 FB 風格」或「讀 MD 資料夾」
3. 🎯 完成 P1（學風格）+ P0（規劃日曆）設定
4. 📱 每天「今天發一篇」，享受自動發文

---

**問題或建議？** 回報 issue：https://github.com/happyaicoding/openclawthreads_skill/issues
