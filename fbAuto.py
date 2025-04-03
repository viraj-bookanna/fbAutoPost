import pickle, time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options

class fbAutoFirefox:
    def __init__(self, headless=True):
        self.logged_in = False
        options = Options()
        if headless:
            options.add_argument("--headless")
        options.add_argument("--start-maximized")
        prefs = {
            "dom.webnotifications.enabled": False,
            "extensions.enabledScopes": 0,
            "general.useragent.override": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Gecko/20100101 Firefox/122.0"
        }
        profile = webdriver.FirefoxProfile()
        for key, value in prefs.items():
            profile.set_preference(key, value)
        options.profile = profile
        self.options = options
        self.driver = None
        with open("script.js", "r") as f:
            self.script = f.read()

    def login(self, cookies_file):
        self.driver = webdriver.Firefox(options=self.options)
        with open(cookies_file, "rb") as f:
            cookies = pickle.load(f)
        self.driver.get("https://facebook.com")
        for cookie in cookies:
            self.driver.add_cookie(cookie)
        self.logged_in = True

    def functionWaiter(self, func_name, argstr='', max_tries=10):
        for _ in range(max_tries):
            if self.driver.execute_script(f"return window.{func_name}({argstr});"):
                return True
            time.sleep(2)
        return False

    def typeText(self, element, text):
        for char in text.replace('\r', ''):
            if char == '\n':
                element.send_keys(Keys.RETURN)
                continue
            element.send_keys(char)

    def sharePost(self, post_link, group, share_text):
        status = False
        self.driver.get(post_link)
        self.driver.execute_script(self.script)
        self.functionWaiter('clickShareBtn')
        self.functionWaiter('clickGroupBtn')
        self.functionWaiter('focusSearch')
        self.typeText(self.driver.switch_to.active_element, group['name'])
        time.sleep(2)
        if self.functionWaiter('selectGroup', f"'{group['link']}'"):
            time.sleep(2)
            self.typeText(self.driver.switch_to.active_element, share_text)
            self.functionWaiter('clickPostBtn')
            time.sleep(2)
            status = True
        return status

    def shareToList(self, jobs, auth):
        if not self.logged_in:
            self.login(auth)
        for job in jobs:
            for group in job['group_list']:
                try:
                    self.sharePost(job['post_link'], group, job['share_text'])
                except Exception as e:
                    print(f"Group {group['name']}\nError: {repr(e)}")

    def close(self):
        self.driver.quit()
