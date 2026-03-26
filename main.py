import os
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi,
    ReplyMessageRequest, TextMessage
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from google import genai

app = Flask(__name__)

LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
gemini_client = genai.Client(api_key=GEMINI_API_KEY)


# ──────────────────────────────────────────
# 刷卡規則（僅限以下六張卡）
# ──────────────────────────────────────────

RULES = [
    {
        "keywords": [
            "國民旅遊卡", "旅遊卡", "訂房", "住宿", "飯店", "旅館", "民宿",
            "hotel", "國旅", "booking", "agoda", "住hotel", "訂hotel",
            "旅宿", "度假", "check in", "checkin", "villa", "背包客棧",
            "hostel", "青年旅館", "溫泉旅館", "商務旅館", "商旅"
        ],
        "card": "玉山銀行國民旅遊卡",
        "rate": "依合作飯店優惠而定",
        "how": "持玉山國民旅遊卡於合作飯店訂房結帳，享政府補助及合作飯店專屬優惠。建議先至玉山官網查詢合作住宿名單再訂房。",
        "caution": "國民旅遊卡限公教人員申辦，消費限合作住宿場所才有優惠，一般消費回饋較低。"
    },
    {
        "keywords": [
            "one for all", "oneforall", "玉山一卡", "玉山one",
            "超商", "7-11", "seven", "全家", "familymart", "萊爾富", "ok超商",
            "早餐", "咖啡", "下午茶", "餐廳", "吃飯", "用餐", "外食",
            "foodpanda", "ubereats", "uber eats", "熊貓外送", "外送",
            "加油", "中油", "台塑石化", "全國電子", "停車",
            "訂閱", "netflix", "spotify", "youtube premium"
        ],
        "card": "玉山 ONE for ALL 卡",
        "rate": "最高 3%（指定通路）",
        "how": "直接刷玉山 ONE for ALL 卡，於指定通路（超商、網購、餐飲等）享最高 3% 回饋，其他通路 0.5%。",
        "caution": "需確認消費通路是否在指定名單內，建議出門前查玉山官網確認最新合作通路。"
    },
    {
        "keywords": [
            "和泰", "toyota", "和泰pay", "中信和泰", "toyotapay",
            "豐田", "lexus", "保養", "車廠", "和泰汽車", "和泰租車",
            "irent", "格上租車", "和運租車", "加油和泰", "和泰加油",
            "和泰集團", "汽車保養", "換機油", "定期保養"
        ],
        "card": "中國信託和泰 Pay 卡",
        "rate": "最高 5%（和泰相關消費）",
        "how": "使用和泰 Pay App 綁定中信和泰 Pay 卡付款，於豐田/和泰相關通路享最高 5% 回饋，一般消費 1%。",
        "caution": "最高回饋限和泰集團相關消費（保養、加油、租車等），一般消費回饋較低。"
    },
    {
        "keywords": [
            "華南love", "love晶緻", "晶緻悠遊", "悠遊聯名", "華南悠遊", "love卡",
            "捷運", "公車", "大眾運輸", "悠遊卡", "mrt", "bus",
            "台北捷運", "高雄捷運", "桃園捷運", "新北捷運",
            "youbike", "ubike", "公共自行車", "腳踏車租借",
            "台鐵", "火車", "區間車", "通勤", "上下班",
            "711", "全家", "超商消費", "ipass", "一卡通"
        ],
        "card": "華南銀行 LOVE 晶緻悠遊聯名卡",
        "rate": "最高 5%（指定通路）",
        "how": "直接刷華南 LOVE 晶緻悠遊聯名卡，超商、捷運、公車等通路最高 5% 回饋。悠遊卡功能可自動加值，搭乘大眾運輸超方便。",
        "caution": "悠遊自動加值功能需先開通，回饋依通路不同有所差異，建議查閱華南官網最新活動。"
    },
    {
        "keywords": [
            "華南i網購", "i網購", "網購生活", "華南jcb", "華南網購", "i卡",
            "momo", "蝦皮", "pchome", "網購", "樂天", "shopee",
            "coupang", "酷澎", "yahoo購物", "yahoo奇摩購物",
            "博客來", "books", "amazon", "friday", "friDay",
            "生活市集", "東森購物", "viva tv", "森森購物",
            "露天拍賣", "奇摩拍賣", "網路購物", "線上購物",
            "電商", "網路下單", "app購物", "手機購物",
            "蝦皮購物", "shopee", "91app", "燦坤線上",
            "全國電子網購", "order online", "線上訂購"
        ],
        "card": "華南銀行 i 網購生活卡（JCB）",
        "rate": "最高 6%（網購通路）",
        "how": "在 momo、蝦皮、PChome、樂天、Coupang 等主要網購平台消費直接刷此卡，享最高 6% 回饋。實體消費也有 1% 基本回饋。",
        "caution": "此卡為 JCB，部分小型網站可能不支援 JCB 付款，建議確認結帳頁面有 JCB 選項再刷。"
    },
    {
        "keywords": [
            "吉鶴", "聯邦吉鶴", "聯邦", "jcb吉鶴",
            "uniqlo", "大創", "daiso", "日系", "日本", "japan",
            "藥妝", "松本清", "唐吉訶德", "免稅", "donki",
            "don quijote", "吉野家", "日本消費", "赴日",
            "無印良品", "muji", "gu", "優衣庫", "nitori",
            "宜得利", "loft", "蔦屋", "tsutaya",
            "日本drugstore", "日藥本舖", "日本藥妝",
            "cosmed japan", "welcia", "マツキヨ", "スギ薬局",
            "tokyu hands", "東急hands", "日本百貨",
            "isetan", "高島屋 japan", "去日本", "日本旅遊購物",
            "日本outlet", "台灣日系", "日本品牌"
        ],
        "card": "聯邦銀行吉鶴卡",
        "rate": "最高 8%（日本/指定通路）",
        "how": "台灣門市（UNIQLO、大創等日系品牌）直接刷或用 Apple Pay / Google Pay 綁吉鶴卡，享 5.5% 回饋。赴日消費於唐吉訶德等指定通路最高 8%（需 Apple Pay QUICPay）。",
        "caution": "吉鶴卡為 JCB，部分小店不支援，月上限 500 元回饋。台灣一般消費回饋較低，建議只在日系通路使用。"
    },
]

CARDS_LIST = "玉山國民旅遊卡、玉山ONE for ALL卡、中信和泰Pay卡、華南LOVE晶緻悠遊聯名卡、華南i網購生活卡(JCB)、聯邦吉鶴卡"

WELCOME_MSG = """👋 你好！我是你的刷卡顧問。

我只推薦以下六張卡的最佳使用方式：
・玉山銀行國民旅遊卡
・玉山 ONE for ALL 卡
・中國信託和泰 Pay 卡
・華南銀行 LOVE 晶緻悠遊聯名卡
・華南銀行 i 網購生活卡（JCB）
・聯邦銀行吉鶴卡

告訴我你要在哪裡消費，我幫你決定刷哪張最划算！

範例：
・去日本買藥妝
・在 momo 網購
・訂飯店住宿
・去 UNIQLO 買衣服
・搭捷運買早餐
・在 Coupang 買東西

直接輸入你的消費情境就好 👇"""


def build_rules_text() -> str:
    lines = []
    for rule in RULES:
        lines.append(f"【關鍵字】{', '.join(rule['keywords'])}")
        lines.append(f"  最佳卡片：{rule['card']}，回饋：{rule['rate']}")
        lines.append(f"  怎麼刷：{rule['how']}")
        if rule.get("backup"):
            lines.append(f"  備選：{rule['backup']}")
        if rule.get("caution"):
            lines.append(f"  注意：{rule['caution']}")
        lines.append("")
    return "\n".join(lines)


SYSTEM_PROMPT = f"""你是一位專業的信用卡刷卡顧問，擅長語意理解，能從使用者描述的消費情境推斷出最適合的通路類別。

【重要限制】你只能從以下六張卡中給建議，絕對不能推薦其他任何卡片：
{CARDS_LIST}

【通路語意分類——請依據這些分類做語意推理】

🛒 網購類（→ 華南 i 網購生活卡 JCB）
包含所有電商平台、網路購物行為，例如：
momo、蝦皮、shopee、PChome、樂天、Yahoo購物、Coupang（酷澎）、
Amazon、博客來、friDay購物、生活市集、東森購物、露天拍賣、
燦坤線上、91APP、任何「網路下單」「線上購物」「app買東西」的行為。
→ 只要是「在網路上買東西」就歸這類。

🇯🇵 日系/日本消費類（→ 聯邦吉鶴卡）
包含日本旅遊購物、台灣日系品牌門市，例如：
UNIQLO、GU、大創、Daiso、無印良品、MUJI、宜得利、Nitori、LOFT、
唐吉訶德、Don Quijote、松本清、日本藥妝店、日本百貨公司、
日本免稅店、任何在日本當地的消費、台灣的日系品牌店面。
→ 只要跟「日本」或「日系品牌」有關就歸這類。

🚇 大眾運輸類（→ 華南 LOVE 晶緻悠遊聯名卡）
包含所有大眾交通工具與相關消費，例如：
捷運、MRT、公車、台鐵、火車、區間車、YouBike、UBike、
悠遊卡加值、通勤、搭車、超商（搭配悠遊卡消費）。
→ 只要是「搭乘交通工具」或「悠遊卡相關」就歸這類。

🏨 住宿/旅遊類（→ 玉山國民旅遊卡，限公教人員）
包含所有住宿訂房消費，例如：
飯店、旅館、民宿、hostel、青年旅館、溫泉旅館、商旅、
Booking.com、Agoda、Hotels.com 等訂房平台消費。
→ 只要是「訂房」「住宿」相關就歸這類（但此卡限公教人員）。

🚗 和泰/豐田相關（→ 中信和泰 Pay 卡）
包含和泰集團旗下所有消費，例如：
Toyota 保養、Lexus 保養、和泰租車、iRent、格上租車、和運租車、
和泰加油站、汽車定期保養、換機油。
→ 只要跟「Toyota/和泰/汽車保養」有關就歸這類。

🏪 日常消費/餐飲類（→ 玉山 ONE for ALL 卡）
包含超商、餐飲、外送等日常消費，例如：
7-11、全家、萊爾富、OK超商、餐廳、早餐店、咖啡廳、
foodpanda、UberEats、訂閱服務（Netflix、Spotify）。
→ 其他通路沒有特別優惠時，日常消費可考慮此卡。

規則表：
{build_rules_text()}

回覆規則：
1. 先用語意理解使用者的消費情境屬於哪個「通路類別」，再從六張卡中選最適合的
2. 如果六張卡都沒有特別優惠的通路，請誠實告知「這六張卡在此通路沒有特別優惠」
3. 用親切口語的繁體中文回覆，不要太正式
4. 回覆格式：
   🏆 最佳選擇：[卡片名稱]
   💰 回饋：[回饋率]

   📋 怎麼刷：
   [說明]

   ⚠️ 注意：[注意事項]（如果有的話）
5. 如果情境不明確，請追問使用者
6. 回覆要簡潔，不要超過 300 字
7. 絕對不可以推薦這六張以外的任何卡片，即使使用者追問也不行"""


def get_advice(text: str) -> str:
    try:
        prompt = f"使用者說：{text}"
        response = gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                {"role": "user", "parts": [{"text": SYSTEM_PROMPT}]},
                {"role": "model", "parts": [{"text": "好的，我明白了。我會根據語意理解來推薦最適合的卡片，只從這六張卡中選擇。"}]},
                {"role": "user", "parts": [{"text": prompt}]}
            ]
        )
        return response.text
    except Exception as e:
        print(f"Gemini error: {e}")
        return get_advice_fallback(text)


def get_advice_fallback(text: str) -> str:
    text_lower = text.lower()
    for rule in RULES:
        for keyword in rule["keywords"]:
            if keyword in text_lower:
                msg = f"🏆 最佳選擇：{rule['card']}\n"
                msg += f"💰 回饋：{rule['rate']}\n\n"
                msg += f"📋 怎麼刷：\n{rule['how']}\n"
                if rule.get("caution"):
                    msg += f"\n⚠️ 注意：{rule['caution']}"
                return msg
    return (
        "🤔 這六張卡在您描述的消費情境沒有特別優惠。\n\n"
        "我只能推薦以下六張卡：\n"
        "・玉山國民旅遊卡\n"
        "・玉山 ONE for ALL 卡\n"
        "・中信和泰 Pay 卡\n"
        "・華南 LOVE 晶緻悠遊聯名卡\n"
        "・華南 i 網購生活卡（JCB）\n"
        "・聯邦吉鶴卡\n\n"
        "可以換個消費情境試試看 😊"
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
    return "LINE 刷卡顧問 Bot 運作中 ✅"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
