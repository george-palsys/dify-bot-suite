from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import TextSendMessage
from logging.handlers import RotatingFileHandler
import os, json, logging, threading
from dify_client import call_dify_workflow

app = Flask(__name__)

# === 初始化 ===
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# === Logging ===
log_file = "/app/logs/flask_webhook.log"
os.makedirs(os.path.dirname(log_file), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=3),
        logging.StreamHandler()
    ],
)
logger = logging.getLogger(__name__)

@app.route("/webhook/linebot", methods=["POST"])
def webhook():
    body = request.get_data(as_text=True)
    signature = request.headers.get("X-Line-Signature", "")

    try:
        handler.handle(body, signature)
        data = json.loads(body)
        for event in data.get("events", []):
            if event.get("type") == "message" and event["message"]["type"] == "text":
                user_id = event["source"]["userId"]
                reply_token = event["replyToken"]
                text = event["message"]["text"]

                # 立即回覆，避免 LINE 超時
                line_bot_api.reply_message(
                    reply_token,
                    TextSendMessage(text="請稍等，我正在處理您的請求...")
                )

                # 背景執行 Dify 工作流
                threading.Thread(target=process_dify_request, args=(text, user_id)).start()

    except InvalidSignatureError:
        logger.warning("簽章驗證失敗")
        return "Invalid signature", 400
    except Exception as e:
        logger.exception("Webhook 錯誤: %s", e)
        return "Server error", 500
    return "OK", 200

def process_dify_request(text, user_id):
    try:
        reply = call_dify_workflow(text)
        line_bot_api.push_message(user_id, TextSendMessage(text=reply))
    except Exception as e:
        logger.exception("推播失敗: %s", e)
        line_bot_api.push_message(user_id, TextSendMessage(text="抱歉，服務暫時不可用。"))

@app.route("/healthz")
def health():
    return "ok", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
