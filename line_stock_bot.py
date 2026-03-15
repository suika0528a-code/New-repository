from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import yfinance as yf
import pandas as pd
import threading
import time

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = "9M9gWuDL+9swPRQtYnGcAfXFwwy1rwlI2b9gBXBhmKv/5yXkdvAMWKCzptxJu0E9paX1nkj88rDh9HUk0mXCvKznM3sTGM9k6upXohJb/+I/civXiL3dU6dp/1Rpz2X+vPvAhMGj5PE5p0L1pCPR7gdB04t89/1O/w1cDnyilFU="
LINE_CHANNEL_SECRET = "f7f7b714907d5efd93a29d5866c9593b"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

alerts = {}

@app.route("/")
def home():
    return "LINE AI STOCK BOT RUNNING"


@app.route("/callback", methods=['POST'])
def callback():

    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)

    try:
        if signature:
            handler.handle(body, signature)
    except:
        pass

    return "OK"


# -----------------------
# 到價提醒
# -----------------------
def check_alerts():

    while True:

        for user_id, alert in list(alerts.items()):

            ticker = alert["ticker"]
            target = alert["price"]

            try:

                stock = yf.Ticker(ticker)
                price = stock.fast_info["last_price"]

                if price >= target:

                    line_bot_api.push_message(
                        user_id,
                        TextSendMessage(
                            text=f"{ticker} 已到 ${target}\n目前價格 ${round(price,2)}"
                        )
                    )

                    del alerts[user_id]

            except:
                pass

        time.sleep(60)


threading.Thread(target=check_alerts, daemon=True).start()


# -----------------------
# LINE 訊息
# -----------------------
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):

    text = event.message.text.strip().upper()
    user_id = event.source.user_id

    try:

        # help
        if text == "HELP":

            msg = """指令

NVDA 查股價
alert NVDA 150

analysis NVDA
rsi NVDA

ai NVDA
hot"""

        # 熱門股
        elif text == "HOT":

            msg = """熱門科技股

NVDA
TSLA
AMD
META
AMZN
MSFT"""

        # AI分析
        elif text.startswith("AI"):

            ticker = text.split(" ")[1]

            data = yf.Ticker(ticker).history(period="5d")

            start = data["Close"].iloc[0]
            end = data["Close"].iloc[-1]

            change = ((end-start)/start)*100

            trend = "多頭" if change > 0 else "空頭"

            msg = f"""{ticker} AI分析

趨勢: {trend}
5日變化: {round(change,2)}%
"""

        # 技術分析
        elif text.startswith("ANALYSIS"):

            ticker = text.split(" ")[1]

            data = yf.Ticker(ticker).history(period="3mo")

            close = data["Close"]

            ma20 = close.rolling(20).mean().iloc[-1]
            ma50 = close.rolling(50).mean().iloc[-1]

            price = close.iloc[-1]

            trend = "多頭" if price > ma20 else "空頭"

            msg = f"""{ticker} 技術分析

價格: ${round(price,2)}

MA20: {round(ma20,2)}
MA50: {round(ma50,2)}

趨勢: {trend}
"""

        # RSI
        elif text.startswith("RSI"):

            ticker = text.split(" ")[1]

            data = yf.Ticker(ticker).history(period="3mo")

            close = data["Close"]

            delta = close.diff()

            gain = delta.clip(lower=0)
            loss = -delta.clip(upper=0)

            avg_gain = gain.rolling(14).mean()
            avg_loss = loss.rolling(14).mean()

            rs = avg_gain / avg_loss
            rsi = 100 - (100/(1+rs))

            rsi_val = rsi.iloc[-1]

            state = "超買" if rsi_val > 70 else "超賣" if rsi_val < 30 else "中性"

            msg = f"""{ticker} RSI

RSI: {round(rsi_val,2)}

狀態: {state}
"""

        # 到價提醒
        elif text.startswith("ALERT"):

            parts = text.split(" ")

            ticker = parts[1]
            target = float(parts[2])

            alerts[user_id] = {
                "ticker": ticker,
                "price": target
            }

            msg = f"已設定 {ticker} 到 ${target} 提醒"

        # 查股價
        else:

            ticker = text

            stock = yf.Ticker(ticker)
            price = stock.fast_info["last_price"]

            msg = f"{ticker} 目前價格 ${round(price,2)}"

    except:

        msg = "請輸入股票代碼，例如 NVDA"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=msg)
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
