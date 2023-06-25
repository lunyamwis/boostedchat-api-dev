import time

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as wait


def close_popup(driver, xpath):
    try:
        wait(driver, 3).until(EC.element_to_be_clickable(driver.find_element(By.XPATH, xpath))).click()
    except TimeoutException:
        print("No popup...")


def close_popup_one(driver, xpath):
    wait(driver, 20).until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, "//iframe[@title='Email Signup']")))
    wait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//span[@class='close top-right']"))).click()


def scroll_gmaps(driver):
    for i in range(6, 25, 3):
        last_review = driver.find_elements(By.CSS_SELECTOR, 'div[jstcache="192"]')
        driver.execute_script("arguments[0].scrollIntoView(true);", last_review[i])
        time.sleep(5)
