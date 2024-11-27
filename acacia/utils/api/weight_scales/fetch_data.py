import frappe
import requests



class FetchData:
    """
    Class to fetch data from the scaling server.
    """

    def __init__(self):
        # Base URL for the scaling server
        self.base_url = "http://65.21.156.159"
        self.batch_details_uri = "/api/accounting/batchdetails/"

    def get_request(self, url, headers=None):
        """
        Send a GET request to the provided URL.
        """
        default_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if not headers:
            headers = default_headers

        response = requests.get(url, headers=headers)
        return response

    def get_batch_details(self, batch_id):
        """
        Fetch batch details using the batch_id from the scaling server.
        """
        url = f"{self.base_url}{self.batch_details_uri}{batch_id}"
        response = self.get_request(url)
        return response

    