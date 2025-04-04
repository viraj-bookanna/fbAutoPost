import pickle, time, traceback
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
            "font.language.group": "unicode",
            "intl.accept_languages": "si-LK,si,en-US,en",
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
        def is_emoji(c):
            return c in ('\U0001F600', '\U0001F64F') or '\U0001F300' <= c <= '\U0001F5FF' or '\U0001F680' <= c <= '\U0001F6FF' or '\U0001F700' <= c <= '\U0001F77F' or '\U0001F780' <= c <= '\U0001F7FF' or '\U0001F800' <= c <= '\U0001F8FF' or '\U0001F900' <= c <= '\U0001F9FF' or '\U0001FA00' <= c <= '\U0001FA6F' or '\U0001FA70' <= c <= '\U0001FAFF'
        def send_emoji(emoji):
            self.driver.execute_script('x=findAll("i",{"aria-label":"Emoji"});return x[x.length-1];').click()
            time.sleep(1)
            try:
                self.driver.execute_script('x=findAll("div",{"aria-label":"Flags"});return x[x.length-1];').click()
                time.sleep(1)
                self.driver.execute_script('x=findAll("img",{alt:"'+emoji+'"});return x[x.length-1];').click()
            except:
                pass
            self.driver.execute_script('x=findAll("div",{"aria-label":"Write something..."});return x[x.length-1];').click()
        for char in text.replace('\r', ''):
            if is_emoji(char):
                send_emoji(char)
            else:
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
                    with open("error.txt", "a") as f:
                        f.write(f"Error: {traceback.format_exc()}\n")

    def close(self):
        self.driver.quit()
