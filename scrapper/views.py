import time

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .helpers.setup import Setup
from .serializers import GmapSerializer, StyleseatSerializer

# Create your views here.


class GmapScrapper(APIView):
    serializer_class = GmapSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        valid = serializer.is_valid(raise_exception=True)
        if valid:
            _, driver = Setup("gmaps").derive_gmap_config()
            driver.get(Setup("gmaps").gmaps_url)
            time.sleep(serializer.data.get("delay"))  # Wait for the page to load dynamically
            search_box = driver.find_element(By.CSS_SELECTOR, serializer.data.get("css_selector_search_box"))
            search_box.send_keys(serializer.data.get("area_of_search"))  # Perform a search
            search_box.submit()
            time.sleep(serializer.data.get("delay"))  # Wait for the search results to load

            result_elements = driver.find_elements(By.CSS_SELECTOR, serializer.data.get("specific_element"))
            results = [element.text.strip() for element in result_elements]

            # Close the browser
            driver.quit()
            status_code = status.HTTP_200_OK

            response = {"success": True, "statusCode": status_code, "results": results}
            return Response(response, status=status_code)


class StyleseatScrapper(APIView):
    serializer_class = StyleseatSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        valid = serializer.is_valid(raise_exception=True)
        if valid:
            _, driver = Setup("styleseat").derive_styleseat_config()
            driver.get(Setup("styleseat").styleseat_url)
            driver.implicitly_wait(20)
            time.sleep(serializer.data.get("delay"))  # Wait for the page to load dynamically
            service_box = driver.find_element(By.XPATH, serializer.data.get("css_selector_service_box"))
            service_box.send_keys(serializer.data.get("service"))
            time.sleep(serializer.data.get("delay"))  # Wait for the search results to load
            area_box = driver.find_element(By.XPATH, serializer.data.get("css_selector_area_box"))
            area_box.clear()
            area_box.send_keys(serializer.data.get("area"))  # Perform a search
            time.sleep(serializer.data.get("delay"))
            button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, serializer.data.get("css_selector_submit_btn")))
            )
            button.click()
            time.sleep(serializer.data.get("delay"))  # Wait for the search results to load

            driver.quit()
            status_code = status.HTTP_200_OK

            response = {"success": True, "statusCode": status_code, "results": []}
            return Response(response, status=status_code)
