import pickle, time, os
from selenium import webdriver
from dotenv import load_dotenv

load_dotenv(override=True)
def setup():
    driver.get("https://facebook.com")
    for cookie in cookies:
        driver.add_cookie(cookie)
    driver.refresh()

input("Please login to Facebook in the browser window open\nYou have 100 seconds to login\npress Enter to continue...")

options = webdriver.ChromeOptions()
driver = webdriver.Chrome(options=options)
if os.path.isfile(os.environ['COOKIES_FILE']):
    with open(os.environ['COOKIES_FILE'], "rb") as f:
        cookies = pickle.load(f)
    setup()

try:
    driver.get("https://facebook.com")
    time.sleep(100)
    cookies = driver.get_cookies()
    with open(os.environ['COOKIES_FILE'], "wb") as f:
        pickle.dump(cookies, f)
finally:
    driver.quit()
