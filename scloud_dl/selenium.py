from pprint import pformat
import undetected_chromedriver as uc

from .credentials import CredentialsProviderBase, Credentials
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common import TimeoutException
import logging
import re
import asyncio
import functools
import operator

logger = logging.getLogger(__name__)

class NetworkCDPInterceptor:

    def __init__(self, method: str):
        self._method: str = method
    
    @property
    def method(self) -> str:
        return self._method
    
    def intercept(self, event) -> None:
        logger.warning(f'{self.intercept.__name__} method not overriden: event received {pformat(event)}')
        pass

class CredentialsRequestInterceptor(NetworkCDPInterceptor):

    RGX_CLIENT_ID: str = r"(.*)\?client_id=(\w*)&.*"
    RGX_USER_ID: str = r"(.*)/stream/users/(\d+)\?(.*)"
    
    
    def __init__(self, method: str):
        super().__init__(method)
        self.__credentials: Credentials = Credentials()
    
    def __find_in_event(self, path: str, event):
        return functools.reduce(operator.getitem, path.split('.'), event)

    def __is_auth_request(self, event):
        params = event.get('params')
        return params and 'XHR' == params.get('type') and params.get('request')
     
    def __has_auth_header(self, event):
        headers = self.__find_in_event('params.request.headers', event)
        return 'Authorization' in headers

    def __extract_client_id(self, url: str) -> str:
        client_id_search = re.search(self.RGX_CLIENT_ID, url)
        return client_id_search.group(2) if client_id_search else None
    
    def __extract_user_id(self, url: str) -> str:
        user_id_search = re.search(self.RGX_USER_ID, url)
        return user_id_search.group(2) if user_id_search else None

    def intercept(self, event):
        if self.__is_auth_request(event) and self.__has_auth_header(event):
            url = self.__find_in_event('params.request.url', event)
            user_id = self.__extract_user_id(url)
            client_id = self.__extract_client_id(url)
            oauth_token: str = self.__find_in_event('params.request.headers.Authorization', event)
            oauth_token = oauth_token.replace('OAuth ', '') if oauth_token else None
            self.__credentials.update(oauth_token, client_id, user_id)

    @property
    def _credentials(self):
        return self.__credentials

    async def poll_credentials(self):
        while not self.__credentials.is_valid:
            await asyncio.sleep(1)
        return self.__credentials


class DriverFactory:

    def __init__(self, interceptors: 'list[NetworkCDPInterceptor]' = []):
        self.__driver: uc.Chrome = None
        self.__interceptors: list[NetworkCDPInterceptor] = interceptors

    def __regeter_interceptors(self, interceptors: 'list[NetworkCDPInterceptor]'):
        for (intercept, method) in map(lambda interceptor: (interceptor.intercept, interceptor.method), interceptors):
            self.__driver.add_cdp_listener(method, intercept)

    @property
    def chrome(self) -> uc.Chrome:
        if self.__driver is not None:
            return self.__driver

        options = uc.ChromeOptions()
        options.add_argument("--disable-gpu")
        options.headless = True
        self.__driver = uc.Chrome(enable_cdp_events=True, keep_alive=False)

        self.__regeter_interceptors(self.__interceptors)

        return self.__driver

class Page:
    def __init__(self, driver_factory: DriverFactory):
        self._driver_factory = driver_factory
    
    def _browser(self):
        return self._driver_factory.chrome

class SoundCloudProfilePage(Page):

    CSS_CONSENT_DIALOG = '#onetrust-consent-sdk'
    CSS_LOGIN_BUTTON = '.loginButton'
    CSS_TAB = '.g-tabs-link'
    CONSENT_DIALOG = (By.CSS_SELECTOR, CSS_CONSENT_DIALOG)
    LOGIN_BUTTON = (By.CSS_SELECTOR, CSS_LOGIN_BUTTON)
    TAB = (By.CSS_SELECTOR, CSS_TAB)

    def __init__(self, driver_factory: DriverFactory):
        super().__init__(driver_factory)

    @staticmethod
    def fprofile_url(
        profile_username): return f"https://www.soundcloud.com/{profile_username}/popular-tracks"

    @staticmethod
    def js_remove_element_by_id(
        element_id): return f'document.getElementById(\'{element_id}\').remove();'

    def navigate_to_profile(self, profile_username: str):
        self._browser().get(self.fprofile_url(profile_username))

    def wait_remove_consent_dialog(self):
        try:
            concent_dialog = WebDriverWait(self._browser(), 5).until(
                EC.visibility_of_element_located(self.CONSENT_DIALOG))

            if concent_dialog.is_displayed():
                self._browser().execute_script(
                    self.js_remove_element_by_id('onetrust-consent-sdk'))
        except TimeoutException:
            logger.warn('consent form was not displayed')
            pass

    def click_on_login_button(self):
        login_button = WebDriverWait(self._browser(), 5).until(
            EC.visibility_of_element_located(self.LOGIN_BUTTON))
        login_button.click()
    
    def click_on_tab(self):
        tab = WebDriverWait(self._browser(), 5).until(
            EC.element_to_be_clickable(self.TAB))
        tab.click()

    
class ProviderIFrame(Page):

    CSS_LOGIN_GOOGLE_BUTTON = '.sc-button-google'
    GOOGLE_LOGIN_BUTTON = (By.CSS_SELECTOR, CSS_LOGIN_GOOGLE_BUTTON)
    
    def __init__(self, driver_factory: DriverFactory):
        super().__init__(driver_factory)

    def switch_to_iframe(self):
        iframes = self._browser().find_elements(By.TAG_NAME, 'iframe')
        for iframe_idx in range(0, len(iframes)):
            self._browser().switch_to.frame(iframe_idx)
            try:
                WebDriverWait(self._browser(), .5).until(
                EC.element_to_be_clickable(self.GOOGLE_LOGIN_BUTTON))
            except TimeoutException:
                self._browser().switch_to.default_content()
            

    def click_on_google(self):
        login_button = self._browser().find_element(*self.GOOGLE_LOGIN_BUTTON)
        login_button.click()
        

class GoogleAuthenticationPopUp(Page):
    CSS_POPUP_LOGIN_NEXT_BUTTON = 'button[jsaction*="click:"]'
    CSS_POPUP_LOGIN_EMAIL = 'input[type="email"]'
    CSS_POPUP_LOGIN_PASS = 'input[type="password"]'
    POPUP_LOGIN_EMAIL = (By.CSS_SELECTOR, CSS_POPUP_LOGIN_EMAIL)
    POPUP_LOGIN_PASS = (By.CSS_SELECTOR, CSS_POPUP_LOGIN_PASS)
    POPUP_LOGIN_NEXT_BUTTON = (By.CSS_SELECTOR, CSS_POPUP_LOGIN_NEXT_BUTTON)
    
    def __init__(self, driver_factory: DriverFactory):
        super().__init__(driver_factory)
    
    def switch_to_login_popup(self):
        popup = self._browser().window_handles[-1]
        self._browser().switch_to.window(popup)

    def type_email(self, email):
        email_input = WebDriverWait(self._browser(), 5).until(
            EC.visibility_of_element_located(self.POPUP_LOGIN_EMAIL))
        email_input.send_keys(email)

    def click_next(self):
        next_button = self._browser().find_elements(*self.POPUP_LOGIN_NEXT_BUTTON)[-2]
        next_button.click()
    
    def type_password(self, password):
        email_input = WebDriverWait(self._browser(), 5).until(
            EC.visibility_of_element_located(self.POPUP_LOGIN_PASS))
        email_input.send_keys(password)

class SeleniumCredentialsProvider(CredentialsProviderBase):
    def __init__(self):
        super().__init__()
        self.__interceptor = CredentialsRequestInterceptor(
            'Network.requestWillBeSent')
        self.__driver_factory = DriverFactory(interceptors=[self.__interceptor])

    async def credentials(self, profile_username):
        credentials = Credentials.load_credentials('./cache/credentials.json')
        if credentials:
            return credentials
        
        chrome = self.__driver_factory.chrome

        profile_page = SoundCloudProfilePage(self.__driver_factory)
        profile_page.navigate_to_profile(profile_username)
        profile_page.wait_remove_consent_dialog()
        profile_page.click_on_login_button()

        credentials = await self.__interceptor.poll_credentials()
        credentials.save_credentials('./cache/credentials.json')
        chrome.close()
        return credentials