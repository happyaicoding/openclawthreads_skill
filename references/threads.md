# Threads 发文（Meta API）

## 概述

使用 Meta Threads API 发文。所有认证信息存于 `config.json`。

**重要**: Threads API 端点与 Instagram 不同
- URL: `https://graph.threads.net/v1.0/` (不是 v18.0)
- 参数: Query Parameters (不是 body)

---

## 参数

- 字数：500 字（超过切成串）
- Hashtag：仅支援**一个**主 topic tag，`#xxx` 纯文字不变连结
- **纯文字 OK**，无需图
- 连结：自动变可点并抓预覽
- 排版：换行、emoji，**无 markdown**

---

## 发文流程（API 版）

### 0. 环境检查

确认 `config.json` 存在，且包含有效的 Threads 认证信息：
- `threads.user_id`
- `threads.access_token`

### 1. 单篇贴文（TEXT）

```
方法: POST
URL: https://graph.threads.net/v1.0/{USER_ID}/threads

Query Parameters:
  - media_type: TEXT
  - text: 贴文内容 (< 500 字)
  - access_token: YOUR_TOKEN
```

**Python 示例:**
```python
import requests

url = "https://graph.threads.net/v1.0/" + user_id + "/threads"
params = {
    'media_type': 'TEXT',
    'text': '你的贴文内容',
    'access_token': access_token
}

resp = requests.post(url, params=params)
# 返回: {"id": "17888878776487688"}
```

### 2. 贴文带图片（IMAGE）

```
Query Parameters:
  - media_type: IMAGE
  - text: 文案 (< 2200 字)
  - image_url: 图片完整 URL
  - access_token: YOUR_TOKEN
```

**Python 示例:**
```python
url = "https://graph.threads.net/v1.0/" + user_id + "/threads"
params = {
    'media_type': 'IMAGE',
    'text': '文案内容',
    'image_url': 'https://example.com/image.jpg',
    'access_token': access_token
}

resp = requests.post(url, params=params)
```

### 3. 分串贴文（> 500 字）

**重要**：Threads API 限制单篇 < 500 字。超过需分串。

```
第一则（鉤子）:
  POST https://graph.threads.net/v1.0/{USER_ID}/threads?
    media_type=TEXT
    &text=<鉤子+主觀點>
    &access_token=<TOKEN>

返回: {"id": "thread_id_1"}

第二则（回复第一则）:
  POST https://graph.threads.net/v1.0/{USER_ID}/threads?
    media_type=TEXT
    &text=<後續內容>
    &reply_to=thread_id_1
    &access_token=<TOKEN>
```

**Python 示例:**
```python
# 发送第一则
first_post = requests.post(url, params={
    'media_type': 'TEXT',
    'text': '鉤子內容',
    'access_token': token
})
thread_id = first_post.json()['id']

# 发送第二则
requests.post(url, params={
    'media_type': 'TEXT',
    'text': '續文',
    'reply_to': thread_id,
    'access_token': token
})
```

### 4. 取得发文链接

发布成功后从 API 响应取得 `id`，构組链接：

```
https://www.threads.net/post/{POST_ID}
```

---

## 生成调性

- 口语、短句、能梗就梗，像「群組聊天的音量」
- 比 FB 鬆、比 X 有呼吸感
- 超 500 字时的分串应在句子边界切，逻辑完整

---

## 错误处理

| 错误碼 | 状况 | 处理 |
|---|---|---|
| 200 | 成功 | 获取 post id，构组链接 |
| 400 Bad Request | 内容不合法（字数超限、参数错误等） | 检查字数 < 500，参数格式正确 |
| 401 Unauthorized | Token 过期或无效 | 执行 token refresh |
| 403 Forbidden | 账号无权限 | 检查账号是否支持 Threads |
| 429 Rate Limit | 发文太频繁 | 等待后重试（见「速率」） |

---

## 速率

- 两篇间至少等 **10 秒**以上
- 分串时：一则一则发，每则间 2-3 秒

---

## Thread 演算法核心差異（vs FB，v0.8 升级）

### 与 FB 演算法 3 大差異

| 维度 | FB 2026 | **Thread 2026** |
|---|---|---|
| 最强信号 | 私訊分享（Messenger）| **转发（repost）** = identity signal |
| 触发机制 | dwell time + 互动 + 私訊 | **keyword detection + 立场分布** |
| 内容偏好 | 长文 + 多媒體 + meta hook | **短文 + 对立立场 + 纯文字** |
| viral 主路径 | 铁粉 → 跨粉絲圈 | **keyword match → 同 ideology 圈广推** |

### 🎯 F4 → F19 进化譜系（v0.8.3 漸進改進路徑）

**对「不敢直接用 TM 級用詞」的創作者**，可以分階段升級：

| 階段 | 加什麼元素 | 預期觸及成長 |
|---|---|---|
| 0 → 1 | + 反差數字（「光昨天 +164」）+ 情緒驚嘆（「太誇張了⋯⋯」）| +20-50% |
| 1 → 2 | + 純粹動機 framing（「興趣而已」「沒差」）| +30-50% |
| 2 → 3 | + 敵人 framing（「付費課程」「韭菜班」）| +100-200% |
| 3 → 4 | + TM 級用詞 + 攻擊性動詞（「就 TM」「幹翻」）| +200-500% |

### ⚠️ Thread 排版鐵則

| 鐵則 | 規格 |
|---|---|
| 段落 | **1 段不換行** |
| 句數 | 2-5 句 |
| 分隔 | **連續逗號 + 「！」分隔**|
| ！級 | 「！」或「！！」|
| 字數 | 60-150 字 |
| emoji | 可有可無 |

### Thread 高 viral keyword 池（2025-2026 實證）

熱門對立 keyword 配對（觸發演算法主動推）：
- 「免費」vs「付費」/「割韭菜」
- 「賺錢」vs「興趣」/「沒差」
- 「公開分享」vs「藏私」
- 「真的」vs「假的」/「TM」
- 「幹翻」/「幹掉」（攻擊性動詞）
- 「韭菜」/「黑粉」/「炒作」

---

## 注意：多账号情况（2026-04 實證）

- **分串一次提交**：每则需分别发布，中途失败整串遗失
- **Token 绑定账号**：config.json 的 `threads.user_id` 决定发文账号

---

**API 已验证可用！** ✅
