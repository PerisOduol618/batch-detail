import frappe, requests

class FetchData:

    '''
    Define a class to interact with the accounting API and fetch data
    '''

    def __init__(self):
        # 1. initialize base Url and endpoint for batch details API
        self.base_url = 'http://65.21.156.159'
        self.batch_details_uri = '/api/accounting/batchdetails/'

    
    def get_request(self, url, headers=None):
        '''
        method to send GET requests to the provided URL.
        '''
        std_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if not headers:
            headers = std_headers

        # Send GET request
        response = requests.get(url, headers=headers)
        
        # Return the response object
        return response
    
    # Method to get data from the API
    def fetch_batch_details(self, batch_id):
        url = f"{self.base_url}{self.batch_details_uri}{batch_id}"

        response = requests.get(url)

        if response.status_code == 200:
            return response.json()
        else:
            return {"error": "Unable to fetch batch details"}

@frappe.whitelist(allow_guest=True)
def receive_notification(*args, **kwargs):
    '''
    Method that receives a notification
    '''
    print(kwargs)

    # 1.Extract batch_id from kwargs
    batch_id = kwargs['batch_id']

    # 2. Call the fetch_batch method to get the batch details
    fetch_data_instance = FetchData()

    # 3. fetch the batch details
    batch_details = fetch_data_instance.fetch_batch_details(batch_id)

    # print(batch_details)

    

    return {'status': True, 'message': "Notification received"}


