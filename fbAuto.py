import pickle, asyncio
from selenium import webdriver

class fbAuto:
    def __init__(self):
        self.logged_in = False
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=0,0')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-gpu')
        self.chrome_options = chrome_options
        self.driver = None
        with open("script.js", "r") as f:
            self.script = f.read()

    async def login(self, cookies_file):
        self.driver = webdriver.Chrome(options=self.chrome_options)
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

    async def sharePost(self, post_link, group, share_text):
        status = False
        self.driver.get(post_link)
        self.driver.execute_script(self.script)
        await self.functionWaiter('clickShareBtn')
        await self.functionWaiter('clickGroupBtn')
        await self.functionWaiter('focusSearch')
        self.driver.switch_to.active_element.send_keys(group['name'])
        if await self.functionWaiter('selectGroup', f"'{group['link']}'"):
            await asyncio.sleep(2)
            self.driver.switch_to.active_element.send_keys(share_text)
            await self.functionWaiter('clickPostBtn')
            await asyncio.sleep(2)
            status = True
        return status
    
    async def close(self):
        self.driver.quit()
