import os

import requests
from bs4 import BeautifulSoup
from selenium import webdriver


class Setup(object):
    def __init__(self, name: str) -> None:
        self.name = name
        self.gmaps_url = "https://www.google.com/maps"
        self.driver = webdriver.Chrome(os.getenv("CHROMEDRIVER_PATH"))

    def derive_gmap_config(self):
        soup = None
        if "gmaps" in self.name:
            response = requests.get(self.gmaps_url)
            html_content = response.text
            soup = BeautifulSoup(html_content, "html.parser")
        else:
            TypeError("Invalid scrapper type")
        return soup, self.driver
