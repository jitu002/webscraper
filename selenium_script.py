from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv
import undetected_chromedriver as uc
import uuid
import time
import random
import requests
import os

load_dotenv()

# Configuration
TWITTER_USERNAME = os.getenv('TWITTER_USERNAME')
TWITTER_PASSWORD = os.getenv('TWITTER_PASSWORD')
MONGO_URI = os.getenv('MONGO_URI')
PROXYMESH_USERNAME = os.getenv('PROXYMESH_USERNAME')
PROXYMESH_PASSWORD = os.getenv('PROXYMESH_PASSWORD')
PROXYMESH_HOST = os.getenv('PROXYMESH_HOST')


def create_driver_options():
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
    return options

def get_ip_info(proxy):
   try:
       response = requests.get('http://ipinfo.io/json', proxies=proxy, timeout=10)
       return response.json()
   except Exception as e:
       print(f"Error getting IP info: {e}")
       return None

def verify_proxy():
   proxy = {
       'http': f'http://{PROXYMESH_USERNAME}:{PROXYMESH_PASSWORD}@{PROXYMESH_HOST}',
       'https': f'http://{PROXYMESH_USERNAME}:{PROXYMESH_PASSWORD}@{PROXYMESH_HOST}'
   }
   ip_info = get_ip_info(proxy)
   if ip_info:
       print(f"Using IP: {ip_info.get('ip')}")
       return True, ip_info
   return False, None


def random_sleep(min_sec=2, max_sec=4):
    time.sleep(random.uniform(min_sec, max_sec))

def fetch_trending_topics():
    driver = None
    
    try:
        print(PROXYMESH_USERNAME)
        proxy_verified, ip_info = verify_proxy()
        if not proxy_verified:
           raise Exception("Proxy verification failed")
        options = create_driver_options()
        driver = uc.Chrome(options=options)
        wait = WebDriverWait(driver, 20)

        # Log in to Twitter
        driver.get("https://twitter.com/i/flow/login")
        random_sleep()

        username_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[autocomplete="username"]')))
        username_input.send_keys(TWITTER_USERNAME)
        random_sleep()
        username_input.send_keys(Keys.RETURN)

        password_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="password"]')))
        password_input.send_keys(TWITTER_PASSWORD)
        random_sleep()
        password_input.send_keys(Keys.RETURN)

        # Navigate to trending topics
        random_sleep()
        driver.get("https://twitter.com/explore")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="trend"]')))
        random_sleep()

        # Fetch trends
        trending_items = driver.find_elements(By.CSS_SELECTOR, '[data-testid="trend"]')[:5]
        trends = [item.text for item in trending_items if item.text]

        # Save data to MongoDB
        client = MongoClient(MONGO_URI)
        db = client["twitter_trends"]
        collection = db["trending_topics"]

        data = {
            "unique_id": str(uuid.uuid4()),
            "trends": trends,
            "timestamp": datetime.now(),
            "ip_data":ip_info
        }
        collection.insert_one(data)
        return data

    except Exception as e:
        import traceback
        print("Error: ", traceback.format_exc())
        return {"error": str(e)}

    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    result = fetch_trending_topics()
    print("Fetched Result:", result)
