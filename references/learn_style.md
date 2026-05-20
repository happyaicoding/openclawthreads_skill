# Phase 1：學風格

## Step 0：選擇素材來源

路由前先問使用者：

> 「要從哪裡學你的語氣風格？
> A：爬你的 Facebook 個人頁（需要提供網址）
> B：讀本機資料夾裡的 MD 文件（需要提供資料夾路徑）」

拿到選擇後開始對應流程。

---

## Option A：從 Facebook 爬取

### 1. 問網址

問使用者 FB 個人頁網址（`facebook.com/username` 或 `facebook.com/profile.php?id=...`）。**不要猜、不要搜尋**。拿到後確認是 `facebook.com` 開頭。

### 2. 導航 + 捲動（重要：FB 個人頁虛擬化）

`browser navigate <使用者網址>`，等 2 秒。**FB 個人頁會虛擬化捲過的貼文（從 DOM 卸載），要邊捲邊抓，不能先滾完再抓。**

捲動要**聚焦在右欄 compose/貼文區**（不是左欄個人資料/朋友/相片）：

```
browser act "scroll down slowly in the main post feed area to load more posts"
```

每次捲動後等 2 秒再繼續。

### 3. 抓貼文（優先自然語言萃取，fallback 全文提取）

**踩過的雷**：FB class name 已 obfuscated；時間戳亂碼但正文乾淨；留言和貼文會混在一起。

**每捲 10-15 ticks，執行一次**：

```
browser extract "extract only the post body text written by the page owner (not comments, not reposts, not shared content). Return each post as a separate item. Skip posts shorter than 8 characters."
```

把結果累積到記憶體集合（用正文前 50 字當 key 去重）。

**Fallback**：萃取結果空或太少，改用：

```
browser extract "all visible text content on the page"
```

用使用者名字重複出現當貼文分界，只保留正文。

**載不動時**：連續兩次 scroll 後貼文數不增加就停手，用目前已收的樣本分析。

### 4. 目標數

**≥ 20 篇乾淨貼文**。若載不到，以實際收到數量為準，在 `style_profile.md` 註明。

---

## Option B：從本機 MD 資料夾讀取

### 1. 問資料夾路徑

問使用者：「請提供 MD 素材資料夾的完整路徑（例：`/home/user/posts` 或 `C:\Users\...\posts`）」

**不要猜預設路徑，不要假設路徑格式**，直接用使用者給的字串。

### 2. 列出資料夾內容

```
system.run ls "<使用者提供的路徑>"
```

（Windows 用 `dir /B "<路徑>"`）

確認有 `.md` 檔案。若資料夾不存在或無 `.md` 檔 → 告知使用者，重新問路徑。

### 3. 逐一讀取 MD 檔案

```
system.run cat "<路徑>/<filename>.md"
```

逐檔讀取，累積所有文字內容到記憶體。過濾掉：
- YAML frontmatter（`---` 之間的區塊）
- 標題行（`#` 開頭）
- 純 code block（\`\`\` 之間）
- 空行過多的分隔符號

只保留**正文段落**作為語氣樣本。

### 4. 目標數

**≥ 10 個段落 / 篇**（MD 素材通常比 FB 貼文長，10 篇即夠）。若不足，告知使用者補充更多 MD 文件或改用 Option A。

---

## 共用：分析面向

不論來源，逐篇/段讀，萃取：

| 面向 | 關鍵提問 |
|---|---|
| 語氣 | 正式/口語/幽默/抒情/碎念？混幾種？ |
| 句長 | 短/中/長？混搭比例？ |
| 標點 | 驚嘆號連發？全/半形？省略號習慣？ |
| 開頭 | 公告型/時間錨/反思/情緒爆點/問句？ |
| 收尾 | 問句/emoji/召集/punchline？ |
| Emoji | 頻率、偏好組合、位置 |
| 主題 | 比例分布 |
| Hashtag | 用/不用/怎麼用 |
| 人稱 | 我/我們的使用 |
| 禁忌 | 沒出現什麼 |
| **高參與度模式** | 明顯受歡迎的段落有無共同結構？→ 寫成 Mode B 模板 |

## 共用：寫入 style_profile.md

完整覆寫，但**保留 `<!-- user-edit -->` 以下的使用者自訂段**（如果既有檔案有）。

格式參考 `style_profile.example.md`：一句話語氣、句式、標點、開頭/收尾、emoji、主題、hashtag、人稱、避免領域、兩種模式的 few-shot 原文、身分線索。

**注意**：若素材來自 MD 資料夾，在 `style_profile.md` 最上方加一行：
```
<!-- source: local-md | path: <使用者提供的路徑> | files: N 個 -->
```

## 共用：給使用者 3 條確認重點

用 3 個 bullet 摘要最顯著特徵，問「準嗎？哪裡歪了直接說。」

- 「準」→ 結束
- 「A 不對應該是 B」→ 對應段落改寫再存
- 「樣本太舊 / 不夠」→ 建議重抓或補充 MD 檔案
