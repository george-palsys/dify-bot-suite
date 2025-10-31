from flask import Flask, request, jsonify
import random, logging, time, os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = Flask(__name__)

# === Logging 設定 ===
logging.basicConfig(
    filename='/app/eip_checkin.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def eip_checkin(username, password):
    # === 隨機打卡時間 (08:40~08:55) ===
    hour = 8
    minute = random.randint(40, 55)
    time_str = f"{hour:02d}:{minute:02d}"
    full_time_str = f"{datetime.now().year}-{datetime.now().month:02d}-{datetime.now().day:02d}-{hour:02d}-{minute:02d}-00"
    logging.info(f"💡 今日打卡時間：{time_str}")

    # === Chrome 選項 ===
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")  # 若要除錯可註解此行
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1366,768")

    driver = webdriver.Chrome(service=Service("/usr/bin/chromedriver"), options=chrome_options)
    wait = WebDriverWait(driver, 15)

    try:
        # === 開啟登入頁 ===
        driver.get("https://eip.palsys.com.tw/UOF/Login.aspx?ReturnUrl=%2fUOF%2fWKF%2fFormUse%2fPersonalBox%2fApplyFormList.aspx%3ffillFormDirectly%3dtrue%26formId%3dClockIn&fillFormDirectly=true&formId=ClockIn")

        # === 登入 ===
        wait.until(EC.element_to_be_clickable((By.ID, "txtAccount"))).send_keys(username)
        wait.until(EC.element_to_be_clickable((By.ID, "txtPwd"))).send_keys(password)
        wait.until(EC.element_to_be_clickable((By.ID, "btnSubmit"))).click()
        time.sleep(5)

        # === 切換 Frame ===
        driver.switch_to.frame(0)
        driver.switch_to.frame(0)

        # === 填寫打卡時間欄位 ===
        # dateInput
        date_input = wait.until(EC.presence_of_element_located((By.ID,
            "ctl00_ContentPlaceHolder1_VersionFieldCollectionUsingUC1_versionFieldUC4_RadTimePicker1_dateInput")))
        driver.execute_script("arguments[0].scrollIntoView(true);", date_input)
        wait.until(EC.element_to_be_clickable((By.ID,
            "ctl00_ContentPlaceHolder1_VersionFieldCollectionUsingUC1_versionFieldUC4_RadTimePicker1_dateInput")))
        date_input.clear()
        date_input.send_keys(time_str)

        # RadTimePicker 主欄位
        time_input = wait.until(EC.presence_of_element_located((By.ID,
            "ctl00_ContentPlaceHolder1_VersionFieldCollectionUsingUC1_versionFieldUC4_RadTimePicker1")))
        driver.execute_script("arguments[0].scrollIntoView(true);", time_input)
        wait.until(EC.element_to_be_clickable((By.ID,
            "ctl00_ContentPlaceHolder1_VersionFieldCollectionUsingUC1_versionFieldUC4_RadTimePicker1")))
        time_input.clear()
        time_input.send_keys(full_time_str)

        # === 點擊送出 ===
        submit_btn1 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#ctl00_MasterPageRadButton3 > .rbText")))
        driver.execute_script("arguments[0].scrollIntoView(true);", submit_btn1)
        submit_btn1.click()

        time.sleep(2)
        submit_btn2 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#ctl00_MasterPageRadButton2 > .rbText")))
        driver.execute_script("arguments[0].scrollIntoView(true);", submit_btn2)
        submit_btn2.click()

        msg = f"✅ 已成功打卡！ ({time_str})"
        logging.info(msg)
        return {"status": "success", "message": msg}

    except Exception as e:
        # === 錯誤時輸出 HTML 與截圖 ===
        ts = int(time.time())
        html_path = f"/app/error_{ts}.html"
        png_path = f"/app/error_{ts}.png"

        try:
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            driver.save_screenshot(png_path)
            logging.error(f"❌ 打卡失敗: {e}，已輸出 {html_path} 與 {png_path}")
        except Exception as log_err:
            logging.error(f"❌ 打卡失敗: {e}（無法輸出HTML）{log_err}")

        return {"status": "error", "message": str(e)}

    finally:
        driver.quit()

# === Flask 路由 ===
@app.route("/run-selenium", methods=["POST"])
def run_selenium():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"status": "error", "message": "缺少 username 或 password"}), 400

    result = eip_checkin(username, password)
    return jsonify(result)

# === 啟動 Flask ===
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8082)

