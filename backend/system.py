import requests

from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.webdriver import WebDriver

from functools import wraps
import re
import json
from typing import Literal

Type = Literal["pass", "catalog"]

class DonationError(Exception):
    pass

class MissingRequiredFields(DonationError):
    pass

class CantBuyItem(DonationError):
    pass

class UnknownTypeError(DonationError):
    pass

class ItemNotFound(DonationError):
    pass

class UnknownError(DonationError):
    pass

class DeleteItemError(DonationError):
    pass

class LoginError(DonationError):
    pass

class Timedout(LoginError):
    pass

class DonationSystem:
    # 5 minutes timeout
    def __init__(self, driver: WebDriver, timeout: float = 300, debug: bool = False):
        self.pass_base_url = "https://www.roblox.com/game-pass/{pass_id}"
        self.revoke_pass_url = "https://www.roblox.com/game-pass/revoke"
        self.delete_from_inventory_url = "https://www.roblox.com/asset/delete-from-inventory"
        self.buy_pass_url = "https://economy.roblox.com/v1/purchases/products/{product_id}"
        self.catalog_url = "https://www.roblox.com/catalog/{catalog_id}"

        self.product_id_regex = re.compile(r"data-product-id=\"([0-9]+)\"")
        self.expected_price_regex = re.compile(r"data-expected-price=\"([0-9]+)\"")
        self.expected_currency_regex = re.compile(r"data-expected-currency=\"([0-9]+)\"")
        self.expected_seller_id_regex = re.compile(r"data-expected-seller-id=\"([0-9]+)\"")
        self.csrf_token_regex = re.compile(r"data-token=\"(.+)\"")

        self.driver = driver
        self.logged_in = False
        self.timeout = timeout
        self.wait = WebDriverWait(driver=driver, timeout=timeout)

        self.session = requests.session()
        self.anonymous_session = requests.session()
        del self.anonymous_session.headers["User-Agent"]

        self.debug = debug

    def debug_only(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if self.debug:
                return func(self, *args, **kwargs)
            else:
                pass

        return wrapper

    def require_logged_in(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if not self.logged_in:
                try:
                    self.login()
                except LoginError as e:
                    print(f"Login error: {e}")
            
            return func(self, *args, **kwargs)

        return wrapper

    @debug_only
    @require_logged_in
    def save_auth(self):
        import pickle
        payload = {
            "session_headers": self.session.headers,
            "cookies": self.user_cookies,
            "session_cookies": self.session.cookies,
        }
        
        with open("saves.pkl", "wb+") as f:
            pickle.dump(payload, f)

    @debug_only
    def load_auth(self):
        import pickle
        
        with open("saves.pkl", "rb") as f:
            payload = pickle.load(f)

        self.session.headers = payload["session_headers"]
        self.user_cookies = payload["cookies"]
        self.session.cookies = payload["session_cookies"]

        self.logged_in = True

    def try_update_csrf(self, html: str):
       csrf_token = self.csrf_token_regex.search(html)
       if csrf_token is not None:
           self.csrf_token = csrf_token.group(1)
           self.session.headers["X-CSRF-TOKEN"] = self.csrf_token

    def login(self):
        """Get login information of the roblox account

        :returns `True` when login succeeds
        """
        #self.driver.get("https://roblox.com/login") # modify to open a new page
        self.driver.execute_script(f'window.open('');')
        self.driver.switch_to.window(self.driver.window_handles[1])
        self.driver.get("https://roblox.com/login")
        try:
            results = self.wait.until(lambda driver: driver.find_element(By.CLASS_NAME, "age-bracket-label-username"))
            csrf_token_meta = self.driver.find_element(By.NAME, "csrf-token")
            self.csrf_token = csrf_token_meta.get_attribute("data-token")
            print(f"[+] Acquired csrf-token")

            self.username = results.text
            print(f"[+] Logged in as {self.username}")

            self.user_cookies = self.driver.get_cookies()
            for cookie in self.user_cookies:
                self.driver.add_cookie(cookie)
                cookie["expiry"] = cookie["expiry"] if "expiry" in cookie.keys() else None
                self.session.cookies.set(cookie["name"], cookie["value"], domain=cookie["domain"], secure=cookie["secure"], expires=cookie["expiry"], path=cookie["path"])
            print(f"[+] Acquired cookies")

            self.user_agent = self.driver.execute_script("return navigator.userAgent;")
            self.session.headers = {
                "User-Agent": self.user_agent,
                "Accept": "*/*",
                "connection": "keep-alive",
                "Referer": "https://www.roblox.com",
                "X-CSRF-TOKEN": self.csrf_token,
            }

            self.logged_in = True

            # for debugging
            self.save_auth()

        except TimeoutException:
            print("[!] Session timed out")
            print("[-] Please try to relog")
            raise Timedout(f"Session timed out. Session time was {self.timeout} second(s).")

    @require_logged_in
    def buy(self, item_id: int | str, type: Type):
        """Get login information of the roblox account

        :param `item_id` is the id of the pass that you want to buy
        """
        # Tried this on tor (the least trust IP) and roblox still returned product ID
        if type == "pass":
            url = self.pass_base_url.format(pass_id=item_id)
        elif type == "catalog":
            url = self.catalog_url.format(catalog_id=item_id)
        else:
            raise UnknownTypeError(f"{type=} is not a known type.")

        response = self.session.get(url)
        if response.status_code == 404:
            raise ItemNotFound(f"Item ID {item_id} doesn't exist for {type}")
        elif response.status_code != 200:
            raise UnknownError(f"Unknown error: {response.status_code=} {response.text=}")

        html = response.text
        self.try_update_csrf(html)
        product_id_option = self.product_id_regex.search(html)
        expected_currency_option = self.expected_currency_regex.search(html)
        expected_price_option = self.expected_price_regex.search(html)
        expected_seller_id_option = self.expected_seller_id_regex.search(html)

        if product_id_option is None or expected_currency_option is None or expected_price_option is None:
            raise MissingRequiredFields(f"Some unknown error happened and {url} did not contain required data about the pass.")

        product_id = product_id_option.group(1)
        expected_currency = expected_currency_option.group(1)
        expected_price = int(expected_price_option.group(1))
        
        if expected_seller_id_option is not None:
            expected_seller_id = expected_seller_id_option.group(1)
        else:
            expected_seller_id = None

        self.session.headers["Content-Type"] = "application/json"
        payload = {
            "expectedCurrency": int(expected_currency),
            "expectedPrice": expected_price,
            "expectedSellerId": expected_seller_id,
        }
        print(payload)
        response = self.session.post(self.buy_pass_url.format(product_id=product_id), data=json.dumps(payload))

        if response.status_code != 200:
            raise CantBuyItem(f"Unable to purchase {url}. {response.status_code=} Returned text: {response.text}")

        try:
            return_status = response.json()

            if not return_status["purchased"]:
                return_status["reason"] = return_status["reason"] if "reason" in return_status.keys() else "No reasons given"

                raise CantBuyItem(f"Unable to purchase {url}. Reason: {return_status['reason']}")

            print(f"[+] Succeeded in purchasing {url}")
        except requests.exceptions.JSONDecodeError:
            pass

    @require_logged_in
    def delete(self, item_id: int | str, type: Type):
        self.session.headers["Content-Type"] = "application/x-www-form-urlencoded"

        if type == "pass":
            url = self.revoke_pass_url
            data = f"id={item_id}"
        elif type == "catalog":
            url = self.delete_from_inventory_url
            data = f"assetId={item_id}"
        else:
            raise UnknownTypeError(f"{type=} is not a known type.")

        response = self.session.post(url, data=data)
        if response.status_code != 200 or not response.json()["isValid"]:
            raise DeleteItemError(f"Unable to delete item {item_id=} of type {type}. Likely due to cookie being expired or this item doesn't exist inside of the inventory. {response.status_code=} {response.text=}")

        print(f"[+] Successfully removed item {url} from inventory")

# test code
def main():
    driver = webdriver.Chrome()
    system = DonationSystem(driver=driver, debug=True)
    system.login()
    #load_auth is only used for debugging
    #system.load_auth()
    system.buy(7159069364, type="catalog")
    system.delete(7159069364, type="catalog")

    input("press enter to continue")

if __name__ == "__main__":
    main()