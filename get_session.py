import pickle, time, os
from selenium import webdriver

options = webdriver.ChromeOptions()
driver = webdriver.Chrome(options=options)

input("Please login to Facebook in the browser window open\nYou have 100 seconds to login\npress Enter to continue...")
try:
    driver.get("https://facebook.com")
    time.sleep(100)
    cookies = driver.get_cookies()
    with open(os.environ['COOKIES_FILE'], "wb") as f:
        pickle.dump(cookies, f)

finally:
    driver.quit()
