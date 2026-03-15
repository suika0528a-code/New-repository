from flask import Flask, request
from linebot.v3.messaging import MessagingApi, Configuration, ApiClient, ReplyMessageRequest, TextMessage
from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks import MessageEvent, TextMessageContent
import yfinance as yf
import os

app = Flask(__name__)


LINE_CHANNEL_ACCESS_TOKEN = "BPQ/+EOBTi0a5fWsab/05yvB8J8v4jsh3zqjk2TqnSoMJ5CsJxU2+RTGKlQx0FndpaX1nkj88rDh9HUk0mXCvKznM3sTGM9k6upXohJb/+JtLYzFboHjcT41gIldo8TNka3g0m8jfe/dgZuU8ll8tAdB04t89/1O/w1cDnyilFU="
LINE_CHANNEL_SECRET = "23cd049315c1c76fc3c115445fe1f650"

configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)


@app.route("/callback", methods=['POST'])
def callback():
    
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except Exception as e:
        print("Webhook error:", e)

    return "OK"


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):

    user_text = event.message.text.strip().upper()

    print("收到訊息:", user_text)

    try:
        stock = yf.Ticker(user_text)
        price = stock.fast_info.get("last_price")

        if price:
            msg = f"{user_text} 目前價格: ${round(price,2)}"
        else:
            msg = "查不到此股票\n請輸入例如：NVDA / TSLA / AAPL"

    except Exception as e:
        print("股票查詢錯誤:", e)
        msg = "股票查詢失敗"

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=msg)]
            )
        )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
