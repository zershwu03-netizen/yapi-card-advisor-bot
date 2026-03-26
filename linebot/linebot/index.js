const express = require("express");
const line = require("@line/bot-sdk");

const config = {
  channelSecret: process.env.LINE_CHANNEL_SECRET,
  channelAccessToken: process.env.LINE_CHANNEL_ACCESS_TOKEN,
};

const client = new line.messagingApi.MessagingApiClient({
  channelAccessToken: config.channelAccessToken,
});

const app = express();
app.use(express.json({ verify: line.middleware(config).rawBodyParser }));

// ── Webhook 接收 ──────────────────────────────────────────
app.post("/webhook", line.middleware(config), async (req, res) => {
  res.sendStatus(200);
  const events = req.body.events || [];
  for (const event of events) {
    if (event.type === "message" && event.message.type === "text") {
      const userText = event.message.text;
      const result = recommend(userText);
      const reply = buildReply(result, userText);
      await client.replyMessage({
        replyToken: event.replyToken,
        messages: [reply],
      });
    }
  }
});

app.get("/", (_, res) => res.send("LINE Bot is running!"));
app.listen(process.env.PORT || 3000, () => console.log("Server started"));

// ── 推薦邏輯 ─────────────────────────────────────────────
function recommend(text) {
  const t = text.toLowerCase();
  const is = (...kws) => kws.some(k => t.includes(k));

  if (is("日本","japan","東京","大阪","京都","北海道","旅日","日幣","quicpay")) {
    return {
      winner: "聯邦吉鶴卡 🇯🇵",
      cashback: "日幣消費 2.5% 無上限",
      reason: "吉鶴卡是旅日首選，搭配 Apple Pay QUICPay 可達 4%。",
      tips: "QUICPay 加碼月上限 1,000 元。",
      others: [["玉山 Unicard", "UP選旅遊特店 4.5%"], ["玉山國民旅遊卡", "旅行社/旅宿適用"]],
    };
  }
  if (is("uniqlo","優衣庫","daiso","大創","日藥","宜得利","nitori","唐吉訶德","donki")) {
    return {
      winner: "聯邦吉鶴卡 🇯🇵",
      cashback: "國內日系名店最高 5.3%",
      reason: "UNIQLO、DAISO 等日系名店加碼 4%，加基本 1.3% 共 5.3%。",
      tips: "日系名店加碼月上限 500 元，百貨店中店不適用。",
      others: [["玉山 Unicard", "任意選設定後 3.5~4%"], ["玉山國民旅遊卡", "基本 1.2%"]],
    };
  }
  if (is("萊爾富","hilife","hi-life")) {
    return {
      winner: "聯邦吉鶴卡 🇯🇵",
      cashback: "萊爾富 5%",
      reason: "吉鶴卡在萊爾富直接享 5% 現金回饋，超商中最高。",
      tips: "需直接刷卡或 Apple/Google Pay，不可用 LINE Pay 或街口。",
      others: [["玉山 Unicard", "超商百大特店 3.5%"], ["聯邦吉鶴卡", "其他超商 1.3%"]],
    };
  }
  if (is("超商","7-11","seven","全家","family","ok mart","ok便利")) {
    return {
      winner: "玉山 Unicard 🎨",
      cashback: "最高 3.5%（簡單選）",
      reason: "Unicard 百大特店涵蓋超商，簡單選直接 3.5% e點，1點=1元。",
      tips: "月回饋上限 1,000 點。萊爾富改用吉鶴卡更優（5%）。",
      others: [["聯邦吉鶴卡", "萊爾富 5%，其他超商 1.3%"], ["玉山國民旅遊卡", "基本 1.2%"]],
    };
  }
  if (is("momo","蝦皮","shopee","pchome","yahoo購物","網購","網路購物","電商","amazon")) {
    return {
      winner: "華南i網購 🛒",
      cashback: "2% 現金回饋",
      reason: "任何電商平台單筆 300 元以上享 2% 現金回饋，LINE Pay/街口也算網購。",
      tips: "需申請電子帳單+綁定 LINE 個人化服務。月上限 200 元（最高刷 10,000 元）。",
      others: [["玉山 Unicard", "百大特店 momo/蝦皮可達 3.5~4.5%"], ["玉山國民旅遊卡", "momo/蝦皮最高 6%"]],
    };
  }
  if (is("全聯","pxmart")) {
    return {
      winner: "玉山 Unicard 🎨",
      cashback: "UP選最高 4.5%",
      reason: "全聯在 Unicard 百大特店內，UP選享 4.5%，簡單選也有 3.5%。",
      tips: "UP選每月訂閱費 149 e點，月上限 5,000 點。",
      others: [["玉山國民旅遊卡", "全聯最高 6%（特定條件）"], ["華南i網購", "行動支付算網購 2%（上限200元）"]],
    };
  }
  if (is("旅遊","旅行","機票","航空","飯店","住宿","訂房","旅行社","高鐵","台鐵","eztravel")) {
    return {
      winner: "玉山國民旅遊卡 🏔️",
      cashback: "旅遊消費最高 8%",
      reason: "搭配 eztravel 國內旅遊享 8% 折扣，高鐵聯票折 3%，旅行社/旅宿皆適用。",
      tips: "主要適合公務人員，需實際旅遊消費才能核銷補助。",
      others: [["玉山 Unicard", "旅遊平台百大特店 UP選 4.5%"], ["聯邦吉鶴卡", "含旅平險、年 2 次免費機場貴賓室"]],
    };
  }
  if (is("toyota","lexus","豐田","凌志","加油","irent","yoxi","和泰","hotai","保修","保養","維修","換油","換胎")) {
    return {
      winner: "中信和泰Pay 🚗",
      cashback: "和泰集團通路最高 10%",
      reason: "保修保養最高 3%，yoxi/iRent 最高 10% 和泰Points，購車 0.6~1% 無上限。",
      tips: "需綁定和泰 Pay 消費。1 和泰Points = 1 元，可折抵保修/車資。",
      others: [["玉山 Unicard", "加油若在百大特店 3.5~4.5%"], ["聯邦吉鶴卡", "國內一般 1.3%"]],
    };
  }
  if (is("捷運","mrt","悠遊","easycard","公車","交通")) {
    return {
      winner: "華南Love晶緻悠遊 🚇",
      cashback: "捷運票價 9 折",
      reason: "整合悠遊卡功能，搭捷運享 9 折，自動加值免手續費，最方便。",
      tips: "現金回饋約 0.4%，純回饋需求建議搭配其他卡。",
      others: [["玉山 Unicard", "交通通路若在百大特店 3.5%"], ["聯邦吉鶴卡", "國內一般 1.3%"]],
    };
  }
  if (is("餐廳","吃飯","外食","foodpanda","ubereats","外送","美食","火鍋","燒烤","聚餐")) {
    return {
      winner: "玉山 Unicard 🎨",
      cashback: "餐飲最高 4.5%（UP選）",
      reason: "Unicard 百大特店涵蓋餐飲通路，UP選 4.5%。也可搭配 LINE Pay/街口任意選享 3.5%。",
      tips: "吉鶴卡指定日系餐廳（一風堂等）現場出示可享最高 10% 現折。",
      others: [["聯邦吉鶴卡", "指定日系餐廳最高現折 10%"], ["玉山國民旅遊卡", "基本 1.2%"]],
    };
  }
  if (is("line pay","linepay","街口","jkos","pi拍","悠遊付","全支付","行動支付")) {
    return {
      winner: "玉山 Unicard 🎨",
      cashback: "行動支付最高 3.5~4%",
      reason: "將 LINE Pay/街口設為 Unicard 任意選特店，不限通路使用該支付均享 3.5~4%。",
      tips: "需在任意選方案中設定，月回饋上限 1,000 點。",
      others: [["華南i網購", "LINE Pay/街口算網購 2%（上限200元）"], ["聯邦吉鶴卡", "國內一般 1.3%"]],
    };
  }
  // 預設
  return {
    winner: "聯邦吉鶴卡 🇯🇵",
    cashback: "國內 1.3% 無上限",
    reason: "一般消費吉鶴卡提供 1.3% 無上限現金回饋（綁定帳戶自扣），是最穩定的兜底選擇。",
    tips: "建議描述具體消費地點或類型，可獲得更精準的推薦。",
    others: [["玉山 Unicard", "確認是否在百大特店，可達 3.5%+"], ["華南i網購", "若屬網購 2%（上限200元）"]],
  };
}

// ── 組裝 LINE Flex Message ───────────────────────────────
function buildReply(r, userText) {
  const othersText = r.others
    .map(([name, note]) => `▸ ${name}：${note}`)
    .join("\n");

  return {
    type: "flex",
    altText: `推薦刷：${r.winner}（${r.cashback}）`,
    contents: {
      type: "bubble",
      styles: { header: { backgroundColor: "#16192a" }, body: { backgroundColor: "#1a1d30" }, footer: { backgroundColor: "#13151f" } },
      header: {
        type: "box", layout: "vertical", contents: [
          { type: "text", text: "💳 信用卡推薦", color: "#8090b8", size: "xs" },
          { type: "text", text: userText, color: "#ffffff", size: "sm", wrap: true, maxLines: 2 },
        ]
      },
      body: {
        type: "box", layout: "vertical", spacing: "md", contents: [
          {
            type: "box", layout: "horizontal", contents: [
              { type: "text", text: "🏆", size: "xxl", flex: 0 },
              {
                type: "box", layout: "vertical", flex: 1, paddingStart: "md", contents: [
                  { type: "text", text: r.winner, color: "#ffd700", weight: "bold", size: "lg" },
                  { type: "text", text: r.cashback, color: "#ffb700", size: "sm" },
                ]
              }
            ]
          },
          { type: "separator", color: "#252840" },
          { type: "text", text: r.reason, color: "#b0b8d8", size: "sm", wrap: true },
          ...(r.tips ? [{ type: "text", text: "⚠️ " + r.tips, color: "#7080a8", size: "xs", wrap: true }] : []),
          { type: "separator", color: "#252840" },
          { type: "text", text: "其他選項", color: "#50607a", size: "xs" },
          { type: "text", text: othersText, color: "#606880", size: "xs", wrap: true },
        ]
      },
      footer: {
        type: "box", layout: "vertical", contents: [
          { type: "text", text: "輸入消費情境即可查詢最優惠的卡", color: "#50607a", size: "xs", align: "center" }
        ]
      }
    }
  };
}
