import json
import logging
import pandas as pd
import time
from typing import Union, Tuple, List, Dict, Generator
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver, WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def start_logging():
    logging.basicConfig(
        level=logging.INFO,
        # filename="stat.log",
        format=("%(asctime)s - %(module)s - " 
             "%(levelname)s - %(funcName)s: "
             "%(lineno)d - %(message)s"),
        datefmt='%H:%M:%S'
    )


def wait_element(
    driver: WebDriver,
    timeout: int, 
    by, 
    selector: str,
    ec = EC.presence_of_element_located
) -> Union[WebElement, None]:
    obj = None
    try: 
        obj = WebDriverWait(driver, timeout).until(
            ec((by, selector))
        )
    except Exception as ex_:
        logging.debug(f"{type(ex_)}, {ex_}")
    
    return obj


def wait_van_element(
    driver: WebDriver,
    timeout: int, 
    by: str, 
    selector: str,
    ec = EC.visibility_of_element_located,
) -> bool:
    try:
        WebDriverWait(driver, timeout).until_not(
            ec((by, selector))
        )
    except Exception as ex_:
        logging.debug(ex_)
        return False
    else:
        return True


class LoginTest:
    def __init__(self, driver: WebDriver, host: str):
        self._driver = driver
        self._host = host


    def signup(self, data: pd.Series):
        if data.get("from_login"):
            self._driver.get(f"{self._host}/login")
            wait_element(
                self._driver, 5, By.CSS_SELECTOR, ".btn-signup").click()
        else:
            self._driver.get(f"{self._host}/signup")
        username = data.get("username") or ""
        name = data.get("name") or ""
        surname = data.get("surname") or ""
        password1 = data.get("password1") or ""
        password2 = data.get("password2") or ""
        wait_element(
            self._driver, 5, By.CSS_SELECTOR, "#id_username"
        ).send_keys(username)
        wait_element(
            self._driver, 5, By.CSS_SELECTOR, "#id_first_name"
        ).send_keys(name)
        wait_element(
            self._driver, 5, By.CSS_SELECTOR, "#id_last_name"
        ).send_keys(surname)
        wait_element(
            self._driver, 5, By.CSS_SELECTOR, "#id_password1"
        ).send_keys(password1)
        wait_element(
            self._driver, 5, By.CSS_SELECTOR, "#id_password2"
        ).send_keys(password2)
        self._driver.find_element(By.CSS_SELECTOR, ".btn-signup").click()
        errors = wait_element(
            self._driver, 5, By.CSS_SELECTOR, ".errors"
        )
        self._driver.delete_all_cookies()
        if errors and errors.text.strip():
            raise ValueError(errors.text)
        

    def signup_users(self, data: pd.DataFrame) -> pd.DataFrame:
        summary = pd.DataFrame(columns=[
            "username", "name", "surname", 
            "password1", "password2", "from_login", 
            "status", "report"
        ])
        for i, row in data.iterrows():
            status = "ok"
            report = None
            try:
                self.signup(row)
            except Exception as ex_:
                status = "fail"
                report = str(ex_)
                logging.info(ex_)
            summary.loc[i] = row.to_dict() | {
                "status": status, "report": report}
        return summary
    

    def login(self, data: pd.Series):
        self._driver.get(f"{self._host}/")
        username = data.get("username") or ""
        password = data.get("password") or ""
        wait_element(
            self._driver, 5, By.CSS_SELECTOR, "#id_username"
        ).send_keys(username)
        wait_element(
            self._driver, 5, By.CSS_SELECTOR, "#id_password"
        ).send_keys(password)
        self._driver.find_element(By.CSS_SELECTOR, ".btn-login").click()
        errors = wait_element(
            self._driver, 1, By.CSS_SELECTOR, ".errors"
        )
        self._driver.delete_all_cookies()
        if errors and errors.text.strip():
            raise ValueError(errors.text)


    def login_users(self, data: pd.DataFrame) -> pd.DataFrame:
        summary = pd.DataFrame(columns=[
            "username", "password", "status", "report"
        ])
        for i, row in data.iterrows():
            status = "ok"
            report = None
            try:
                self.login(row)
            except Exception as ex_:
                status = "fail"
                report = str(ex_)
                logging.debug(ex_)
            summary.loc[i] = row.to_dict() | {
                "status": status, "report": report}
        return summary


class TestConference:
    def __init__(self, driver: WebDriver, host: str, actions_path: str):
        self._driver = driver
        self._host = host
        with open(actions_path) as f:
            data = json.load(f)
        self._actions = data


    def signup(self, data: dict):
        if data.get("from_login"):
            self._driver.get(f"{self._host}/login")
            wait_element(
                self._driver, 5, By.CSS_SELECTOR, ".btn-signup").click()
        else:
            self._driver.get(f"{self._host}/signup")
        username = data.get("username") or ""
        name = data.get("name") or ""
        surname = data.get("surname") or ""
        password1 = data.get("password1") or ""
        password2 = data.get("password2") or ""
        wait_element(
            self._driver, 5, By.CSS_SELECTOR, "#id_username"
        ).send_keys(username)
        wait_element(
            self._driver, 5, By.CSS_SELECTOR, "#id_first_name"
        ).send_keys(name)
        wait_element(
            self._driver, 5, By.CSS_SELECTOR, "#id_last_name"
        ).send_keys(surname)
        wait_element(
            self._driver, 5, By.CSS_SELECTOR, "#id_password1"
        ).send_keys(password1)
        wait_element(
            self._driver, 5, By.CSS_SELECTOR, "#id_password2"
        ).send_keys(password2)
        self._driver.find_element(By.CSS_SELECTOR, ".btn-signup").click()
        errors = wait_element(
            self._driver, 5, By.CSS_SELECTOR, ".errors"
        )
        self._driver.delete_all_cookies()
        if errors and errors.text.strip():
            raise ValueError(errors.text)


    def login(self, data: dict):
        self._driver.get(f"{self._host}/login")
        username = data.get("username") or ""
        password = data.get("password") or ""
        wait_element(
            self._driver, 5, By.CSS_SELECTOR, "#id_username"
        ).send_keys(username)
        wait_element(
            self._driver, 5, By.CSS_SELECTOR, "#id_password"
        ).send_keys(password)
        self._driver.find_element(By.CSS_SELECTOR, ".btn-login").click()
        errors = wait_element(
            self._driver, 1, By.CSS_SELECTOR, ".errors"
        )
        self._driver.delete_all_cookies()
        if errors and errors.text.strip():
            raise ValueError(errors.text)


    def logout(self, data: dict):
        self._driver.get(f"{self._host}/logout")
        self._driver.delete_all_cookies()


    def connect(self, data: dict):
        # .audio-toggle
        # .video-toggle
        # #Join-Room
        # #Leave-back
        pass


    def run_user(self, data: list[dict]):
        self._driver.execute_cdp_cmd("Browser.grantPermissions", {
            "origin": self._host,
            "permissions": [
                "geolocation", "audioCapture", 
                "displayCapture", "videoCapture",
                "videoCapturePanTiltZoom"
            ]
        })
        funcs = {
            "signup": self.signup,
            "login": self.login,
            "connect": self.connect
        }
        for d in data:
            funcs[d["action"]](d["data"])


class Runner:
    def __init__(
        self, host: str, 
        signup_action_path: str, login_action_path: str, 
        signup_action_report_path: str, login_action_report_path: str
    ):
        self._host = host
        self._signup_data = pd.read_csv(signup_action_path)
        self._login_data = pd.read_csv(login_action_path)
        self._signup_report_path = signup_action_report_path
        self._login_report_path = login_action_report_path


    def run(self):
        with webdriver.Firefox() as driver:
            logging.info("run tester")
            lt = LoginTest(driver, self._host)
            logging.info("start signup test")
            signup_report = lt.signup_users(self._signup_data)
            signup_report.to_csv(self._signup_report_path)
            logging.info("end signup test")
            logging.info("start login test")
            login_report = lt.login_users(self._login_data)
            login_report.to_csv(self._login_report_path)
            logging.info("end login test")
            logging.info("end test")
            logging.info("save reports")


def main():
    start_logging()
    runner = Runner(
        "http://127.0.0.1:8000",
        "data/signup_data.csv",
        "data/login_data.csv",
        "reports/signup_data.csv",
        "reports/login_data.csv"
    )
    runner.run()


if __name__ == "__main__":
    main()