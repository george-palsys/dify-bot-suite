# line-bot-dify

一個整合 **LINE Messaging API** 與 **Dify Workflow** 的 Flask 應用。
此專案可接收使用者訊息，呼叫 Dify 取得 AI 回覆後再推播回 LINE 使用者。
以 Docker Compose 容器化部署。

---

## 🚀 快速啟動

### 1️⃣ 複製設定檔

```bash
cp .env.example .env
# 編輯 .env 填入你的 LINE 與 Dify 金鑰
```

### 2️⃣ 啟動容器

```bash
docker compose up -d --build
```

### 3️⃣ 健康檢查

```bash
curl http://localhost:5000/healthz
```

如果返回：

```
ok
```

代表 Flask webhook 正常啟動。

---

## 🔗 LINE Webhook URL

請在 LINE Developer 後台設定：

```
https://<你的網域或 ngrok URL>/webhook/linebot
```

點選「Verify」應顯示：

```
Success ✅
```

---

## ⚙️ 環境變數說明

| 變數名稱                        | 說明                                                             |
| --------------------------- | -------------------------------------------------------------- |
| `LINE_CHANNEL_ACCESS_TOKEN` | 你的 LINE Bot Access Token                                       |
| `LINE_CHANNEL_SECRET`       | 你的 LINE Bot Channel Secret                                     |
| `DIFY_API_KEY`              | Dify Workflow API 金鑰                                           |
| `DIFY_WORKFLOW_URL`         | Dify Workflow 執行端點，例如：`http://192.168.30.161/v1/workflows/run` |

---

## 🧱 專案結構

```
line-bot-dify/
├── app.py                # Flask 主程式
├── dify_client.py        # 呼叫 Dify API 模組
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── logs/                 # Log 檔掛載資料夾
└── README.md
```

---

## 🧩 日誌位置

容器內：

```
/app/logs/flask_webhook.log
```

若透過 docker-compose，會自動掛載到主機：

```
./logs/
```

---

## 🧪 測試

開啟 LINE App 傳訊息給 Bot，例如：

```
你好
```

Bot 應回覆：

```
請稍等，我正在處理您的請求...
```

約 30 秒後收到 Dify AI 回覆。

---

## 🧰 停止與重啟

```bash
docker compose down
docker compose up -d
```

---

## 🧾 授權

MIT License

