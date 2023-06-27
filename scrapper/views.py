import time

from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from instagram.models import Account

from .helpers.setup import Setup
from .models import Links
from .serializers import (
    GmapSerializer,
    GmapsProfileSerializer,
    InstagramSerializer,
    StyleseatProfileSerializer,
    StyleseatSerializer,
)

# Create your views here.


class GmapScrapper(APIView):
    serializer_class = GmapSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        valid = serializer.is_valid(raise_exception=True)
        results = []
        if valid:
            _, driver = Setup("gmaps").derive_gmap_config()
            driver.get(Setup("gmaps").gmaps_url)
            time.sleep(serializer.data.get("delay"))  # Wait for the page to load dynamically
            search_box = driver.find_element(By.CSS_SELECTOR, serializer.data.get("css_selector_search_box"))
            search_box.send_keys(serializer.data.get("area_of_search"))  # Perform a search
            search = driver.find_element(By.XPATH, serializer.data.get("search_button"))
            search.click()
            time.sleep(serializer.data.get("delay"))  # Wait for the search results to load
            time.sleep(serializer.data.get("delay"))  # Wait for the search results to load

            divSideBar = None
            try:
                divSideBar = driver.find_element(
                    By.CSS_SELECTOR, f"div[aria-label='Matokeo ya {serializer.data.get('area_of_search')}']"
                )
            except NoSuchElementException as err:
                print(err)
                try:
                    divSideBar = driver.find_element(
                        By.CSS_SELECTOR, f"div[aria-label='Results of {serializer.data.get('area_of_search')}']"
                    )
                except NoSuchElementException as err:
                    print(err)

            keepScrolling = True
            while keepScrolling:
                divSideBar.send_keys(Keys.PAGE_DOWN)
                time.sleep(3)
                divSideBar.send_keys(Keys.PAGE_DOWN)
                time.sleep(3)
                html = driver.find_element(By.TAG_NAME, "html").get_attribute("outerHTML")
                Links.objects.all().delete()
                links = divSideBar.find_elements(By.TAG_NAME, "a")
                for element in links:

                    results.append(element.get_attribute("href"))
                    link = Links()
                    link.url = element.get_attribute("href")
                    link.source = 1
                    link.save()

                if html.find("You've reached the end of the list.") != -1:
                    keepScrolling = False
                elif html.find("Umefikia mwisho wa orodha.") != -1:
                    keepScrolling = False

            driver.quit()
            status_code = status.HTTP_200_OK

            response = {"success": True, "statusCode": status_code, "results": results}
            return Response(response, status=status_code)


class GmapsProfiles(viewsets.ViewSet):
    serializer_class = GmapsProfileSerializer

    def create(self, request):
        links = Links.objects.filter(source=1)
        response = None
        status_code = None
        success = None
        for link in links:
            _, driver = Setup("gmaps").derive_styleseat_config()
            driver.get(link.url)
            time.sleep(4)
            account = Account()
            try:
                account.gmaps_business_name = driver.find_element(By.XPATH, request.data.get("xpath_business")).text
                time.sleep(2)
            except NoSuchElementException:
                print("Did not find that element moving on to next")
            try:
                account.review = float(driver.find_element(By.XPATH, request.data.get("xpath_review")).text)
                time.sleep(2)
            except NoSuchElementException:
                print("Did not find that element moving on to next")
            status_code = status.HTTP_200_OK
            success = True
            account.is_from_styleseat = False
            account.save()

        response = {"success": success, "status": status_code}
        return Response(response)


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
            time.sleep(serializer.data.get("delay"))  # Wait for the search results to load
            time.sleep(serializer.data.get("delay"))  # Wait for the search results to load
            url_list = []
            list_of_seats = None
            try:
                list_of_seats = driver.find_elements(By.XPATH, serializer.data.get("css_selector_seats"))
            except TimeoutException:
                print("No popup...")

            for seat in list_of_seats:

                names = None
                try:
                    names = seat.find_elements(By.TAG_NAME, "h3")
                except NoSuchElementException:
                    print("escape")
                for name in names:
                    name.click()
                    time.sleep(4)

            Links.objects.all().delete()
            for window in range(1, len(driver.window_handles)):
                try:
                    driver.switch_to.window(driver.window_handles[window])
                except IndexError as err:
                    print(f"{err}")

                url_list.append(driver.current_url)
                link = Links()
                link.url = driver.current_url
                link.source = 2
                link.save()

            driver.switch_to.window(driver.window_handles[0])
            driver.quit()
            status_code = status.HTTP_200_OK

            response = {"success": True, "statusCode": status_code, "results": url_list}
            return Response(response, status=status_code)


class StyleSeatScrapperProfiles(viewsets.ViewSet):
    serializer_class = StyleseatProfileSerializer

    def create(self, request):
        links = Links.objects.filter(source=1)
        response = None
        status_code = None
        success = None
        for link in links:
            _, driver = Setup("styleseat").derive_styleseat_config()
            driver.get(link.url)
            time.sleep(7)
            account = Account()
            try:
                account.igname = driver.find_element(By.XPATH, request.data.get("xpath_ig_username")).text
                time.sleep(2)
            except NoSuchElementException:
                print("Did not find that element moving on to next")
            try:
                account.review = float(driver.find_element(By.XPATH, request.data.get("xpath_review")).text)
                time.sleep(2)
            except NoSuchElementException:
                print("Did not find that element moving on to next")
            status_code = status.HTTP_200_OK
            success = True
            account.save()

        response = {"success": success, "status": status_code}
        return Response(response)

    def retrieve(self, request, pk=None):
        queryset = Links.objects.all()
        link = get_object_or_404(queryset, pk=pk)
        status_code = status.HTTP_200_OK
        response = {"link": link.url, "status": status_code}
        return Response(response, status=status_code)


class InstagramScrapper(viewsets.ViewSet):
    serializer_class = InstagramSerializer

    def search_users(self, request, *args, **kwargs):
        accounts = Account.objects.all()
        links = []
        status_code = 0

        time.sleep(2)
        driver = Setup("instagram").instagram_login()
        time.sleep(5)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Not Now']"))).click()
        time.sleep(8)
        for account in accounts:
            if account.gmaps_business_name:
                driver.find_elements(By.XPATH, "//a[contains(@class,'x1i10hfl')]")[2].click()
                time.sleep(3)

                searchbox = WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.XPATH, "//input[@placeholder='Search']"))
                )

                # send search into input

                searchbox.send_keys(account.gmaps_business_name)
                time.sleep(2)
                # searchbox.submit()

                searchbox.send_keys(Keys.ENTER)
                time.sleep(1)
                searchbox.send_keys(Keys.ENTER)
                time.sleep(7)
                account.igname = driver.current_url.split("/")[-2:][0]
                account.profile_url = driver.current_url
                links.append(driver.current_url)
                account.save()
                status_code = 200

        return Response({"status_code": status_code, "links": links})
