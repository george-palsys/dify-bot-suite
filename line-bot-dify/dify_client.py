import os, requests, json, logging

logger = logging.getLogger(__name__)

def call_dify_workflow(user_message):
    """
    呼叫 Dify Workflow API 並回傳結果
    """
    DIFY_API_KEY = os.getenv("DIFY_API_KEY")
    DIFY_WORKFLOW_URL = os.getenv("DIFY_WORKFLOW_URL")

    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "inputs": {"check": user_message},
        "user": "line-user"
    }

    try:
        logger.info("呼叫 Dify: %s", json.dumps(payload, ensure_ascii=False))
        response = requests.post(DIFY_WORKFLOW_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        outputs = data.get("data", {}).get("outputs", {})
        for key in ("Response_result", "result", "text"):
            if key in outputs:
                return outputs[key]
        return "抱歉，我暫時無法回答您的問題。"

    except Exception as e:
        logger.error("Dify 呼叫錯誤: %s", e)
        return "抱歉，服務暫時不可用。"
