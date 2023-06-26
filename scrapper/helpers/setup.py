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
        self.instagram_url = "https://www.instagram.com/martinlunyamwi"
        self.driver = webdriver.Chrome()

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
        username = "martinlunyamwi"
        password = "luther1996-"

        getdriver = "https://www.instagram.com/accounts/login/"

        self.driver.get(getdriver)

        time.sleep(4)

        self.driver.find_element(By.XPATH, '//*[@id="loginForm"]/div/div[1]/div/label/input').send_keys(username)
        self.driver.find_element(By.XPATH, '//*[@id="loginForm"]/div/div[2]/div/label/input').send_keys(password)
        self.driver.find_element(By.XPATH, '//*[@id="loginForm"]/div/div[3]/button').click()
        return self.driver
