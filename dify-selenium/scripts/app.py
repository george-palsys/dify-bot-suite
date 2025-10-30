from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import base64, time, traceback

app = Flask(__name__)

@app.route('/run-selenium', methods=['POST'])
def run_selenium():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"status": "error", "message": "username and password required"}), 400

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu")

    service = Service("/usr/bin/chromedriver")

    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get("https://palsys.hrmax.104.com.tw/")

        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".btn")))
        username_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder='登入帳號 Account']")
        password_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder='登入密碼 Password']")
        username_input.send_keys(username)
        password_input.send_keys(password)
        driver.find_element(By.CSS_SELECTOR, ".btn").click()

        time.sleep(5)
        driver.refresh()
        WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn-primary")))
        driver.find_element(By.CSS_SELECTOR, ".btn-primary").click()

        time.sleep(2)
        target_value = driver.find_element(By.CSS_SELECTOR, "ul:nth-child(4) > li:nth-child(1) > span").text

        png = driver.get_screenshot_as_png()
        encoded_img = base64.b64encode(png).decode('utf-8')

        result = {
            "status": "success",
            "message": f"打卡成功，目標值：{target_value}",
        }

    except Exception as e:
        traceback.print_exc()
        result = {"status": "error", "message": f"Exception: {str(e)}"}
    finally:
        if 'driver' in locals():
            driver.quit()

    return jsonify(result)


@app.route('/healthz')
def health():
    return "ok", 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081)

