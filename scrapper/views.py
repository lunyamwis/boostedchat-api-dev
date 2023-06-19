import time

from helpers.setup import Setup
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import GmapSerializer

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
            search_box = driver.find_element_by_css_selector(serializer.data.get("css_selector_search_box"))
            search_box.send_keys(serializer.data.get("area_of_search"))  # Perform a search
            search_box.submit()
            time.sleep(serializer.data.get("delay"))  # Wait for the search results to load

            result_elements = driver.find_elements_by_css_selector(serializer.data.get("specific_element"))
            results = [element.text.strip() for element in result_elements]

            # Close the browser
            driver.quit()
            status_code = status.HTTP_200_OK

            response = {"success": True, "statusCode": status_code, "results": results}
            return Response(response, status=status_code)
