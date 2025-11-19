import time
import json
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

class WeChatAuth:
    def __init__(self, cookie_file="wechat_cookies.json"):
        self.base_url = "https://mp.weixin.qq.com/"
        self.driver = None
        self.token = None
        self.cookies = None
        self.cookie_file = cookie_file

    def save_cookies(self):
        """保存 cookies 到文件"""
        if self.cookies and self.token:
            data = {
                "token": self.token,
                "cookies": self.cookies
            }
            with open(self.cookie_file, "w") as f:
                json.dump(data, f)
            print(f"Cookies已保存到 {self.cookie_file}")

    def load_cookies(self):
        """从文件加载 cookies"""
        if os.path.exists(self.cookie_file):
            try:
                with open(self.cookie_file, "r") as f:
                    data = json.load(f)
                self.token = data.get("token")
                self.cookies = data.get("cookies")
                print("已从文件加载Cookies。")
                return True
            except Exception as e:
                print(f"加载cookies失败: {e}")
                return False
        return False

    def login(self):
        """
        Logs in to WeChat Public Platform using Selenium.
        Waits for manual QR code scan.
        """
        print("正在启动浏览器进行登录...")
        options = webdriver.ChromeOptions()
        # options.add_argument('--headless') # Cannot use headless for QR code scan
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.get(self.base_url)

        print("请扫描二维码登录。")
        
        try:
            # Wait for the URL to change, indicating successful login
            # The URL usually changes to something like https://mp.weixin.qq.com/cgi-bin/home?t=home/index&lang=zh_CN&token=...
            WebDriverWait(self.driver, 120).until(
                EC.url_contains("cgi-bin/home")
            )
            print("登录成功!")
            
            # Extract token from URL
            current_url = self.driver.current_url
            self.token = current_url.split("token=")[1].split("&")[0]
            print(f"已获取Token: {self.token}")

            # Extract cookies
            selenium_cookies = self.driver.get_cookies()
            self.cookies = {cookie['name']: cookie['value'] for cookie in selenium_cookies}
            
            # Save cookies for future use
            self.save_cookies()
            
            # Keep the browser open or close it? 
            # For now, we can close it as we have the cookies/token, 
            # but sometimes keeping it open prevents session expiry.
            # Let's close it for now to save resources, reopen if needed.
            self.driver.quit()
            return self.token, self.cookies

        except Exception as e:
            print(f"登录失败或超时: {e}")
            if self.driver:
                self.driver.quit()
            return None, None

if __name__ == "__main__":
    auth = WeChatAuth()
    auth.login()
