from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from random import randint
import os, time, traceback, shutil

app = Flask(__name__)

CHROMEDRIVER_PATH = "/usr/bin/chromedriver"
screenshot_dir = "/app/scripts"
tmp_user_data_dir = "/tmp/selenium-user-data"

# 建立 headless Chrome
def create_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument(f"--user-data-dir={tmp_user_data_dir}")
    service = Service(CHROMEDRIVER_PATH)
    return webdriver.Chrome(service=service, options=chrome_options)

# 遞迴搜尋 iframe 中的「確定」按鈕
def find_confirm_button_in_iframes(driver):
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    for iframe in iframes:
        try:
            driver.switch_to.frame(iframe)
            confirm_btn = WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#ctl00_MasterPageRadButton2 > .rbText"))
            )
            return confirm_btn
        except:
            pass
        btn = find_confirm_button_in_iframes(driver)
        if btn:
            return btn
        driver.switch_to.parent_frame()
    return None

def generate_random_time():
    hour, minute = 8, randint(40, 55)
    return f"{hour:02d}:{minute:02d} AM"

@app.route('/run-selenium', methods=['POST'])
def run_selenium():
    driver = None
    try:
        data = request.get_json()
        username, password = data.get("username"), data.get("password")

        if not username or not password:
            return jsonify({"status": "error", "message": "缺少 username 或 password"}), 400

        print("=== 開始執行 Selenium 打卡腳本 ===")
        driver = create_driver()
        driver.get("https://eip.palsys.com.tw/UOF/Login.aspx?ReturnUrl=%2fUOF%2fWKF%2fFormUse%2fPersonalBox%2fApplyFormList.aspx%3ffillFormDirectly%3dtrue%26formId%3dClockIn&fillFormDirectly=true&formId=ClockIn")

        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "txtAccount")))
        driver.find_element(By.ID, "txtAccount").send_keys(username)
        driver.find_element(By.ID, "txtPwd").send_keys(password)
        driver.find_element(By.ID, "btnSubmit").click()
        time.sleep(5)

        # 進入內層 iframe
        WebDriverWait(driver, 10).until(EC.frame_to_be_available_and_switch_to_it((By.TAG_NAME, "iframe")))
        WebDriverWait(driver, 10).until(EC.frame_to_be_available_and_switch_to_it((By.TAG_NAME, "iframe")))

        random_time = generate_random_time()
        print(f"準備填入打卡時間: {random_time}")

        time_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_VersionFieldCollectionUsingUC1_versionFieldUC4_RadTimePicker1_dateInput"))
        )
        time_input.clear()
        time_input.send_keys(random_time)
        time_input.send_keys(Keys.TAB)

        # 送出表單
        submit_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "ctl00_MasterPageRadButton3"))
        )
        driver.execute_script("arguments[0].click();", submit_btn)
        print("表單送出完成。")

        driver.switch_to.default_content()
        confirm_btn = find_confirm_button_in_iframes(driver)
        if confirm_btn:
            driver.execute_script("arguments[0].click();", confirm_btn)
            print("已點擊『確定』。")
        else:
            print("⚠️ 未找到『確定』按鈕。")

        msg = f"✅ 已成功打卡！({random_time})"
        print(msg)
        return jsonify({"status": "success", "message": msg})

    except Exception as e:
        traceback.print_exc()
        try:
            if driver:
                driver.save_screenshot(os.path.join(screenshot_dir, "error.png"))
        except:
            pass
        msg = f"❌ 打卡失敗: {str(e)}"
        return jsonify({"status": "error", "message": msg})

    finally:
        if driver:
            driver.quit()
        shutil.rmtree(tmp_user_data_dir, ignore_errors=True)
        print("=== Selenium 打卡腳本結束 ===")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8082)

