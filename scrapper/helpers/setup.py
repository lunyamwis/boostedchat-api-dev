import os
import time

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By


class Setup(object):
    def __init__(self, name: str) -> None:
        self.name = name
        self.gmaps_url = "https://www.google.com/maps"
        self.styleseat_url = "https://www.styleseat.com"
        self.instagram_url = "https://www.instagram.com/"
        self.options = webdriver.ChromeOptions()
        self.options.add_argument("--headless")
        self.options.add_argument("start-maximized")  # open Browser in maximized mode
        self.options.add_argument("disable-infobars")  # disabling infobars
        self.options.add_argument("--disable-extensions")  # disabling extensions
        self.options.add_argument("--disable-gpu")  # applicable to windows os only
        self.options.add_argument("--disable-dev-shm-usage")  # overcome limited resource problems
        self.options.add_argument("--no-sandbox")  # Bypass OS security model
        self.driver = webdriver.Chrome(options=self.options)

    def derive_gmap_config(self):
        soup = None
        if "gmaps" in self.name:
            response = requests.get(self.gmaps_url)
            html_content = response.text
            soup = BeautifulSoup(html_content, "html.parser")
        else:
            TypeError("Invalid scrapper type")
        return soup, self.driver

    def derive_styleseat_config(self):
        soup = None
        if "style" in self.name:
            response = requests.get(self.gmaps_url)
            html_content = response.text
            soup = BeautifulSoup(html_content, "html.parser")
        else:
            TypeError("Invalid scrapper type")
        return soup, self.driver

    def instagram_login(self):
        username = os.getenv("IG_USERNAME")
        password = os.getenv("IG_PASSWORD")

        getdriver = "https://www.instagram.com/accounts/login/"

        self.driver.get(getdriver)

        time.sleep(4)

        self.driver.find_element(By.XPATH, '//*[@id="loginForm"]/div/div[1]/div/label/input').send_keys(username)
        time.sleep(4)
        self.driver.find_element(By.XPATH, '//*[@id="loginForm"]/div/div[2]/div/label/input').send_keys(password)
        time.sleep(4)
        self.driver.find_element(By.XPATH, '//*[@id="loginForm"]/div/div[3]/button').click()
        time.sleep(3)
        return self.driver
