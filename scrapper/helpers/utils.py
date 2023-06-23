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
