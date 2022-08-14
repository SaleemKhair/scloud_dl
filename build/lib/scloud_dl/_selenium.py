from pprint import pformat
import undetected_chromedriver as uc
from .credentials import CredentialsProviderBase, Credentials
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
import re
import asyncio

logger = logging.getLogger(__name__)


class DriverFactory:

    def __init__(self):
        self.__driver: uc.Chrome = None

    def __apply_handlers(self, handlers: 'list[tuple]'):
        [self.__driver.add_cdp_listener(event_name, on_event)
         for (on_event, event_name) in handlers]

    def driver(self, handlers: 'list[tuple]') -> uc.Chrome:
        if self.__driver is not None:
            return self.__driver

        options = uc.ChromeOptions()
        options.add_argument("--disable-gpu")
        self.__driver = uc.Chrome(enable_cdp_events=True, keep_alive=False)

        if handlers:
            self.__apply_handlers(handlers)

        return self.__driver


class CredentialsAwareInterceptor:

    RGX_CLIENT_ID: str = r"(.*)\?client_id=(\w*)&.*"
    RGX_USER_ID: str = r"(.*)/stream/users/(\d+)\?(.*)"

    def __init__(self, method: str):
        self.__credentials: Credentials = Credentials()
        self.__method = method

    @property
    def method(self):
        return self.__method

    def on_request(self, event):
        if event.get('params') and 'XHR' == event['params']['type'] and event['params'].get('request'):
            logger.debug(
                f'request event recieved: {pformat(event.get("params").get("request"))}')
            url = event['params']['request']['url']
            user_id_search = re.search(self.RGX_USER_ID, url)
            client_id_search = re.search(self.RGX_CLIENT_ID, url)

            user_id = user_id_search.group(2) if user_id_search else None
            client_id = client_id_search.group(2) if client_id_search else None
            oauth_token: str = event['params']['request']['headers'].get(
                'Authorization')
            oauth_token = oauth_token.replace(
                'OAuth ', '') if oauth_token else None
            self.__credentials.update(
                oauth_token=oauth_token,
                client_id=client_id,
                user_id=user_id
            )

    async def poll_credentials(self):
        while not self.__credentials.is_valid:
            await asyncio.sleep(1)
        return self.__credentials


class SoundCloudProfilePage:

    CSS_CONSENT_DIALOG = '#onetrust-consent-sdk'
    CSS_LOGIN_BUTTON = '.loginButton'
    CSS_LOGIN_GOOGLE_BUTTON = 'button.google-plus-signin.sc-button-google'
    CSS_POPUP_LOGIN_EMAIL = 'input[type="email"]'
    CSS_POPUP_LOGIN_NEXT_BUTTON = 'button[jsaction*="click:"]'
    CONSENT_DIALOG = (By.CSS_SELECTOR, CSS_CONSENT_DIALOG)
    LOGIN_BUTTON = (By.CSS_SELECTOR, CSS_LOGIN_BUTTON)
    GOOGLE_LOGIN_BUTTON = (By.CSS_SELECTOR, CSS_LOGIN_GOOGLE_BUTTON)
    POPUP_LOGIN_EMAIL = (By.CSS_SELECTOR, CSS_LOGIN_GOOGLE_BUTTON)
    POPUP_LOGIN_NEXT_BUTTON = (By.CSS_SELECTOR, CSS_LOGIN_GOOGLE_BUTTON)

    @staticmethod
    def fprofile_url(
        profile_username): return f"https://www.soundcloud.com/{profile_username}/popular-tracks"

    @staticmethod
    def js_remove_element_by_id(
        element_id): return f'document.getElementById(\'{element_id}\').remove();'

    def __init__(self, driver_factory: DriverFactory, interceptor: CredentialsAwareInterceptor):
        self.__driver_factory: DriverFactory = driver_factory
        self.__interceptor: CredentialsAwareInterceptor = interceptor

    def __browser(self):
        return self.__driver_factory.driver([(self.__interceptor.on_request, self.__interceptor.method)])

    def navigate_to_profile(self, profile_username: str):
        self.__browser().get(self.fprofile_url(profile_username))

    def wait_remove_consent_dialog(self):
        concent_dialog = WebDriverWait(self.__browser(), 5).until(
            EC.visibility_of_element_located(self.CONSENT_DIALOG))

        if concent_dialog.is_displayed():
            self.__browser().execute_script(
                self.js_remove_element_by_id('onetrust-consent-sdk'))

    def click_on_login_button(self):
        login_button = self.__browser().find_element(*self.LOGIN_BUTTON)
        login_button.click()

    def click_on_google(self):
        google_provider_button = self.__browser().find_element(*self.GOOGLE_LOGIN_BUTTON)
        google_provider_button.click()

    def switch_to_login_popup(self):
        popup = self.__browser().window_handles[-1]
        self.__browser().switch_to.window(popup)

    def type_email(self, email):
        email_input = self.__browser().find_element(self.POPUP_LOGIN_EMAIL)
        email_input.send_keys(email)

    def click_next(self):
        next_button = self.__browser().find_element(self.POPUP_LOGIN_NEXT_BUTTON)
        next_button.click()
    

class SeleniumCredentialsProvider(CredentialsProviderBase):
    def __init__(self):
        super().__init__()
        self.__interceptor = CredentialsAwareInterceptor(
            'Network.requestWillBeSent')
        self.__page = SoundCloudProfilePage(
            DriverFactory(), self.__interceptor)

    async def credentials(self, profile_username):

        self.__page.navigate_to_profile(profile_username)
        self.__page.wait_remove_consent_dialog()
        self.__page.click_on_login_button()
        self.__page.click_on_google()

        self.__page.switch_to_login_popup()
        self.__page.type_email('saleemkhair@gmail.com')
        self.__page.click_next()

        return await self.__interceptor.poll_credentials()
