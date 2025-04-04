import pickle, time, os
from selenium import webdriver
from dotenv import load_dotenv
from selenium.webdriver.firefox.options import Options

load_dotenv(override=True)
options = Options()
options.add_argument("--start-maximized")
prefs = {
    "dom.webnotifications.enabled": False,
    "extensions.enabledScopes": 0,
    "font.language.group": "unicode",
    "intl.accept_languages": "si-LK,si,en-US,en",
}
profile = webdriver.FirefoxProfile()
for key, value in prefs.items():
    profile.set_preference(key, value)
options.profile = profile
driver = webdriver.Firefox(options=options)
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
