# 信用卡推薦 LINE Bot

## 設定步驟

### 1. LINE Developers 設定
1. 前往 https://developers.line.biz
2. 建立 Provider → 建立 Messaging API channel
3. 記下：Channel Secret、Channel Access Token（長期）

### 2. 部署到 Render（免費）
1. 將此資料夾上傳到 GitHub（新建 repo）
2. 前往 https://render.com，連結 GitHub repo
3. 建立 Web Service，設定：
   - Build Command: `npm install`
   - Start Command: `npm start`
4. 在 Environment Variables 加入：
   - `LINE_CHANNEL_SECRET` = 你的 Channel Secret
   - `LINE_CHANNEL_ACCESS_TOKEN` = 你的 Access Token

### 3. 設定 Webhook
1. 複製 Render 的網址（例如 https://your-app.onrender.com）
2. 在 LINE Developers → Messaging API → Webhook URL 填入：
   `https://your-app.onrender.com/webhook`
3. 開啟 Use webhook
4. 關閉 Auto-reply messages

### 使用方式
在 LINE 聊天室直接輸入消費情境，例如：
- 「在momo買東西」
- 「去日本旅遊」
- 「Toyota保養」
- 「超商便利商店」
