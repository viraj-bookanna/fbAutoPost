import pickle, asyncio
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.keys import Keys

class fbAuto:
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

    async def login(self, cookies_file):
        self.driver = webdriver.Firefox(options=self.options)
        with open(cookies_file, "rb") as f:
            cookies = pickle.load(f)
        self.driver.get("https://facebook.com")
        for cookie in cookies:
            self.driver.add_cookie(cookie)
        self.logged_in = True

    async def functionWaiter(self, func_name, argstr='', max_tries=10):
        for _ in range(max_tries):
            if self.driver.execute_script(f"return window.{func_name}({argstr});"):
                return True
            await asyncio.sleep(2)
        return False

    async def typeText(self, element, text):
        for char in text.replace('\r', ''):
            if char == '\n':
                element.send_keys(Keys.RETURN)
                continue
            element.send_keys(char)

    async def sharePost(self, post_link, group, share_text):
        status = False
        self.driver.get(post_link)
        self.driver.execute_script(self.script)
        await self.functionWaiter('clickShareBtn')
        await self.functionWaiter('clickGroupBtn')
        await self.functionWaiter('focusSearch')
        await self.typeText(self, self.driver.switch_to.active_element, group['name'])
        await asyncio.sleep(2)
        if await self.functionWaiter('selectGroup', f"'{group['link']}'"):
            await asyncio.sleep(2)
            await self.typeText(self.driver.switch_to.active_element, share_text)
            await self.functionWaiter('clickPostBtn')
            await asyncio.sleep(2)
            status = True
        return status
    
    async def close(self):
        self.driver.quit()
