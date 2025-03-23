import pickle, time, os
from selenium import webdriver

options = webdriver.ChromeOptions()
driver = webdriver.Chrome(options=options)
with open(os.environ['COOKIES_FILE'], "rb") as f:
    cookies = pickle.load(f)

def setup():
    driver.get("https://facebook.com")
    for cookie in cookies:
        driver.add_cookie(cookie)
    driver.refresh()

setup()
while True:
    try:
        if not driver.window_handles:
            break
        time.sleep(1)
    except:
        break

driver.quit()
