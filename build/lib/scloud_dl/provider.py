import asyncio
import logging
from dataclasses import dataclass, asdict
from pprint import pformat
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
import re
import json
import os

logger = logging.getLogger(__name__)


@dataclass
class Credentials:
    oauth_token: str = None
    client_id: str = None
    user_id: int = None

    @property
    def __dict__(self):
        """
        get a python dictionary
        """
        return asdict(self)

    @property
    def json(self):
        """
        get the json formated string
        """
        return json.dumps(self.__dict__)
    
    def is_ready(self) -> bool:
        return self.user_id and self.client_id and self.oauth_token


class OnRequestWillBeSentHandler:
    RGX_CLIENT_ID: str = r"(.*)\?client_id=(\w*)&.*"
    RGX_USER_ID: str = r"(.*)/stream/users/(\d+)\?(.*)"

    @staticmethod
    def on_request_will_be_sent(fn_update):

        def on_event(event):

            if event.get('params') and 'XHR' == event['params']['type'] and event['params'].get('request'):
                logger.debug(
                    f'request event recieved: {pformat(event.get("params").get("request"))}')
                url = event['params']['request']['url']
                user_id_search = re.search(
                    OnRequestWillBeSentHandler.RGX_USER_ID, url)
                user_id = user_id_search.group(2) if user_id_search else None
                client_id_search = re.search(
                    OnRequestWillBeSentHandler.RGX_CLIENT_ID, url)
                client_id = client_id_search.group(
                    2) if client_id_search else None
                oauth_token: str = event['params']['request']['headers'].get(
                    'Authorization')
                oauth_token = oauth_token.replace(
                    'OAuth ', '') if oauth_token else None
                fn_update(
                    Credentials(
                        user_id=user_id,
                        client_id=client_id,
                        oauth_token=oauth_token
                    )
                )

        return on_event


class DriverFactory:
    def get_driver(self, handlers: 'list[tuple]') -> uc.Chrome:

        options = uc.ChromeOptions()
        options.add_argument("--disable-gpu")
        options.set_capability(
            "goog:loggingPrefs", {"performance": "ALL", "browser": "ALL"}
        )
        driver = uc.Chrome(enable_cdp_events=True, keep_alive=False)
        [driver.add_cdp_listener(event_name, on_event)
         for (on_event, event_name) in handlers]
        return driver


class SeleniumCredentialsProvider:

    def __init__(self):
        self._browser: uc.Chrome = None
        self._credentials: Credentials = Credentials()

    def _update_credentials(self, credentials: Credentials):
        self._credentials.client_id = credentials.client_id if credentials.client_id else self._credentials.client_id
        self._credentials.user_id = credentials.user_id if credentials.user_id else self._credentials.user_id
        self._credentials.oauth_token = credentials.oauth_token if credentials.oauth_token else self._credentials.oauth_token

    def _save_credentials(self):
        with open('./sc_credentials.txt', 'w') as f:
            f.write(self._credentials.json)
            f.flush()
    
    def _load_credentials(self) -> Credentials:
        credentials_file = './sc_credentials.txt'
        if os.path.exists(credentials_file):
            with open(credentials_file, 'r') as f:
                return Credentials(**json.load(f))
        return None
    def _navigate_to_login(self, user_name):
        self._browser.get(
            f"https://www.soundcloud.com/{user_name}/popular-tracks")
        try:
            concent_dialog = WebDriverWait(self._browser, 2).until(
            EC.visibility_of_element_located((By.ID, 'onetrust-consent-sdk')))
            if concent_dialog.is_displayed():
                self._browser.execute_script(
                    f'document.getElementById(\'onetrust-consent-sdk\').remove();')
        except: #noqa
            pass 

        login_button = self._browser.find_element(
            By.CSS_SELECTOR, '.loginButton')
        login_button.click()

    async def get_credentials(self, user_name: str) -> Credentials:
        saved_credentials = None
        try:
            saved_credentials = self._load_credentials()
        except:
            pass

        if saved_credentials:
            return saved_credentials

        handler = OnRequestWillBeSentHandler()
        self._browser = DriverFactory().get_driver(handlers=[
            (handler.on_request_will_be_sent(
                self._update_credentials), 'Network.requestWillBeSent')
        ])
        try:
            self._navigate_to_login(user_name)

            while not self._credentials.is_ready():
                await asyncio.sleep(1)

            logger.info(f'credentials:{pformat(self._credentials)}')
            self._save_credentials()
            return self._credentials
        except Exception:
            logger.exception('error in webderiver', exc_info=1)
        finally:
            self._browser.close()
