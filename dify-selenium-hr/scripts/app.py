from flask import Flask, request, jsonify
import logging, time, os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = Flask(__name__)

# Logging
logging.basicConfig(
    filename='/app/hr_checkin.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

HR_LOGIN_URL = "https://palsys.hrmax.104.com.tw/"
CHROMEDRIVER_PATH = "/usr/bin/chromedriver"


def run_hr_checkin(username, password):
    timestamp = int(time.time())
    err_html = f"/app/hr_error_{timestamp}.html"
    err_png = f"/app/hr_error_{timestamp}.png"

    # Selenium options
    chrome_options = Options()
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1366,768")

    try:
        driver = webdriver.Chrome(
            service=Service(CHROMEDRIVER_PATH),
            options=chrome_options
        )

        logging.info("Navigating to HR login page...")
        driver.get(HR_LOGIN_URL)

        # 等待登入框
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".btn"))
        )

        # 帳號
        username_input = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,
                                            "input[placeholder='登入帳號 Account']"))
        )
        username_input.clear()
        username_input.send_keys(username)

        # 密碼
        password_input = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,
                                            "input[placeholder='登入密碼 Password']"))
        )
        password_input.clear()
        password_input.send_keys(password)

        # 登入
        login_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn"))
        )
        login_button.click()

        # Login 後刷新
        time.sleep(5)
        driver.refresh()

        # 找 "我要打卡"
        clock_in_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn-primary"))
        )
        clock_in_button.click()

        time.sleep(2)
        target_value = driver.find_element(
            By.CSS_SELECTOR,
            "ul:nth-child(4) > li:nth-child(1) > span"
        ).text

        logging.info(f"打卡成功：{target_value}")

        driver.quit()
        return {
            "status": "success",
            "message": f"打卡成功：{target_value}"
        }

    except Exception as e:
        logging.error(f"HR 打卡失敗: {e}")

        # 儲存 HTML
        try:
            with open(err_html, "w") as f:
                f.write(driver.page_source)
        except:
            pass

        # Screenshot
        try:
            driver.save_screenshot(err_png)
        except:
            pass

        driver.quit()

        return {
            "status": "error",
            "message": str(e),
            "html": err_html,
            "png": err_png
        }


@app.route("/run-selenium", methods=["POST"])
def run_selenium():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"status": "error", "message": "缺少 username 或 password"}), 400

    result = run_hr_checkin(username, password)
    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081)

