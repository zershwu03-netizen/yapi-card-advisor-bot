import os
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi,
    ReplyMessageRequest, TextMessage
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

app = Flask(__name__)

LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")

configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)


# ──────────────────────────────────────────
# 刷卡規則判斷邏輯
# ──────────────────────────────────────────

RULES = [
    {
        "keywords": ["蝦皮", "shopee", "momo", "pchome", "yahoo購物", "網購", "線上購物", "網路購物"],
        "card": "華南 i 網購生活卡",
        "rate": "2%",
        "how": "直接用華南 i 網購生活卡刷卡付款。需申請電子帳單並綁定華南銀行 LINE 官方帳號個人化通知服務，單筆 300 元以上享 2% 現金回饋，每期回饋上限 200 元。",
        "backup": "玉山 Unicard UP選 4.5%（若已開通，百大特店含蝦皮/momo）",
        "caution": "回饋上限每期 200 元（約刷 10,000 元），超過額度建議改用玉山 Unicard。"
    },
    {
        "keywords": ["line pay", "街口", "行動支付", "open錢包", "掃碼"],
        "card": "華南 i 網購生活卡",
        "rate": "2%",
        "how": "華南 i 網購卡認定範圍寬鬆，LINE Pay、街口支付等行動支付也算網購通路，享 2% 現金回饋。直接綁定 i 網購卡至行動支付 App 消費即可。",
        "backup": "玉山 Unicard 任意選 3.5%（選行動支付為指定特店）",
        "caution": "每期回饋上限 200 元，大額消費建議搭配 Unicard。"
    },
    {
        "keywords": ["toyota", "lexus", "豐田", "和泰", "保養", "修車", "買車", "yoxi", "irent", "租車"],
        "card": "中信和泰 Pay 聯名卡",
        "rate": "最高 6%",
        "how": "下載和泰 Pay App，綁定中信和泰聯名卡。在 TOYOTA/Lexus 保養、修車、iRent 租車、yoxi 叫車等和泰集團通路消費享最高 6% 和泰 Points 回饋。1 點 = 1 元，可折抵下次和泰相關消費。",
        "backup": "玉山國民旅遊卡（一般消費 1%，搭乘旅遊有加成）",
        "caution": "需綁定和泰 Pay 才享加碼回饋，未綁定僅享基本 1%。"
    },
    {
        "keywords": ["加油", "中油", "台塑", "全國加油", "油站"],
        "card": "中信和泰 Pay 聯名卡",
        "rate": "2%",
        "how": "直接刷中信和泰聯名卡加油，享 2% 和泰 Points 回饋。若有綁定和泰 Pay 效果更好。",
        "backup": "華南 Love 晶緻悠遊卡（加油有紅利回饋）",
        "caution": "中信和泰卡的加油回饋是 2%，屬量販/加油通路固定回饋。"
    },
    {
        "keywords": ["日本", "韓國", "旅遊", "出國", "海外", "國外", "旅行"],
        "card": "聯邦吉鶴卡",
        "rate": "最高 8%（日本）",
        "how": "日本旅遊直接刷聯邦吉鶴卡，日幣消費 2.5% 無上限。若有 iPhone，用 Apple Pay 綁吉鶴卡以 QUICPay 感應付款，前月帳單滿 3 萬可再加碼 2.5%，合計最高 5%。指定通路（唐吉訶德/UNIQLO/藥妝等）加碼 3%，最高 8%。",
        "backup": "玉山 Unicard 玩旅刷（UP選）4.5% 海外消費",
        "caution": "聯邦吉鶴卡是 JCB，部分小店不支援，建議準備備用卡。韓國消費同樣適用 2.5% 無上限。"
    },
    {
        "keywords": ["uniqlo", "大創", "daiso", "don don donki", "唐吉訶德", "宜得利"],
        "card": "聯邦吉鶴卡",
        "rate": "5.5%（台灣門市）",
        "how": "在台灣 UNIQLO / 大創 / 唐吉訶德直接刷聯邦吉鶴卡實體卡，或用 Apple Pay / Google Pay 綁吉鶴卡付款，享 5.5% 回饋，月上限 500 元。",
        "backup": "玉山 Unicard UP選 4.5%",
        "caution": "吉鶴卡月上限 500 元（約刷 9,000 元），超過後改刷 Unicard。"
    },
    {
        "keywords": ["旅館", "飯店", "住宿", "訂房", "國內旅遊", "國旅", "klook", "kkday"],
        "card": "玉山國民旅遊卡",
        "rate": "最高 1.2%",
        "how": "刷玉山國民旅遊卡，國內旅遊住宿、旅行社、訂房平台消費享回饋。需申請電子帳單並設定玉山帳戶自動扣繳享最高 1.2% 玉山 e point 回饋。",
        "backup": "中信和泰卡去趣旅遊商城 2%（yoxi/iRent/HOTAI購等）",
        "caution": "國民旅遊卡若為公務員版，享有額外公務補助；一般民間版回饋較低，建議大額旅遊消費考慮其他卡。"
    },
    {
        "keywords": ["百貨", "新光三越", "sogo", "遠東", "漢神", "微風", "誠品", "購物中心"],
        "card": "玉山 Unicard",
        "rate": "最高 4.5%（UP選）",
        "how": "每月底前在玉山 Wallet App 切換至「UP選」方案，並將該百貨加入指定特店，當月消費享 4.5% e point 回饋，月上限 5,000 點。若不想管方案就刷「簡單選」享 3%。",
        "backup": "聯邦吉鶴卡（一般消費 1%，百貨無特別加碼）",
        "caution": "UP選需每月訂閱 149 點，建議月消費超過 3,000 元以上才值得訂閱。"
    },
    {
        "keywords": ["超商", "7-11", "711", "全家", "familymart", "萊爾富", "hilife", "ok超商"],
        "card": "聯邦吉鶴卡",
        "rate": "5%（萊爾富）",
        "how": "萊爾富超商直接刷聯邦吉鶴卡實體卡，或用 Apple Pay / Google Pay，享 5% 折扣無上限。其他超商（7-11/全家）建議用玉山 Unicard 簡單選 3%。",
        "backup": "玉山 Unicard 天天刷 3%（7-11/全家/量販均適用）",
        "caution": "7-11 和全家建議用 Unicard，萊爾富則吉鶴卡最划算。"
    },
    {
        "keywords": ["餐廳", "吃飯", "餐飲", "外食", "美食", "火鍋", "燒肉", "壽司"],
        "card": "玉山 Unicard",
        "rate": "最高 4.5%（UP選 好饗刷）",
        "how": "每月底在玉山 Wallet 切換「UP選」，並將餐廳加入指定特店（或選全台餐飲類），直接刷實體卡享 4.5% 回饋。",
        "backup": "華南 Love 晶緻悠遊卡（紅利回饋，換算約 1~2%）",
        "caution": "Unicard 需實體卡或 Apple Pay/Google Pay 直刷，不能透過 LINE Pay/街口 間接享特店回饋。"
    },
    {
        "keywords": ["捷運", "公車", "交通", "高鐵", "台鐵", "悠遊卡", "加值"],
        "card": "華南 Love 晶緻悠遊聯名卡",
        "rate": "紅利2倍（自動加值）",
        "how": "Love 晶緻悠遊卡本身有悠遊卡功能，設定自動加值，當期帳單消費達 1,000 元以上，悠遊卡自動加值享 2 倍紅利回饋。搭捷運直接感應此卡即可。",
        "backup": "玉山國民旅遊卡（高鐵自由座感應，高鐵乘車有紅利加成）",
        "caution": "Love 卡的紅利回饋需兌換商品，非直接現金，使用彈性較低。"
    },
    {
        "keywords": ["保費", "保險", "壽險", "車險", "產險"],
        "card": "玉山 Unicard",
        "rate": "1%",
        "how": "直接刷玉山 Unicard 繳保費，享基本 1% e point 回饋，無上限。",
        "backup": "中信和泰聯名卡（保費屬一般消費，享基本 1%）",
        "caution": "這 6 張卡的保費回饋都不高，約 1%，建議選平時最常用的卡繳即可。"
    },
    {
        "keywords": ["一般", "其他", "不知道", "隨便", "都可以"],
        "card": "玉山 Unicard（簡單選）",
        "rate": "3%",
        "how": "玉山 Unicard 切換「簡單選」，百大特店通路享 3% 回饋，月上限 1,000 點（可刷 5 萬元）。不需要每天切換，只要月底前確認方案即可。",
        "backup": "華南 i 網購生活卡 2%（網購/行動支付）",
        "caution": "Unicard 需搭配玉山帳戶自動扣繳 + 電子帳單才享完整 3%。"
    },
]

WELCOME_MSG = """👋 你好！我是你的刷卡顧問。

告訴我你要在哪裡消費，我幫你決定刷哪張卡、怎麼刷最划算！

你持有的卡片：
💳 玉山國民旅遊卡
💳 玉山 Unicard
💳 中信和泰 Pay 聯名卡
💳 華南 Love 晶緻悠遊聯名卡
💳 華南 i 網購生活卡
💳 聯邦吉鶴卡

範例：
・蝦皮網購
・TOYOTA 保養
・去日本旅遊
・訂 UNIQLO
・去萊爾富買東西
・搭捷運

直接輸入消費情境就好 👇"""


def get_advice(text: str) -> str:
    text_lower = text.lower()

    for rule in RULES:
        for keyword in rule["keywords"]:
            if keyword in text_lower:
                msg = f"🏆 最佳選擇：{rule['card']}\n"
                msg += f"💰 回饋：{rule['rate']}\n\n"
                msg += f"📋 怎麼刷：\n{rule['how']}\n"

                if rule.get("backup"):
                    msg += f"\n🥈 備選：{rule['backup']}\n"

                if rule.get("caution"):
                    msg += f"\n⚠️ 注意：{rule['caution']}"

                return msg

    return (
        "🤔 我不太確定這個消費情境，建議直接刷：\n\n"
        "🏆 玉山 Unicard（簡單選）\n"
        "💰 回饋：3%（百大特店）\n\n"
        "📋 怎麼刷：\n直接刷卡，月底前確認玉山 Wallet 已切換「簡單選」即可。\n\n"
        "💡 你可以試著描述更多細節，例如：\n"
        "「蝦皮網購」、「去萊爾富」、「日本旅遊」等"
    )


# ──────────────────────────────────────────
# LINE Webhook
# ──────────────────────────────────────────

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_text = event.message.text.strip()

    if user_text.lower() in ["你好", "hi", "hello", "開始", "help", "說明", "?"]:
        reply = WELCOME_MSG
    else:
        reply = get_advice(user_text)

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply)]
            )
        )


@app.route("/", methods=["GET"])
def index():
    return "LINE 刷卡顧問 Bot（家人版）運作中 ✅"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
