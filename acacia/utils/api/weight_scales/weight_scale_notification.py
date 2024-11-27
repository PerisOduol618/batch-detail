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
    try:

        # 1.Extract batch_id from kwargs
        batch_id = kwargs['batch_id']
        if not batch_id:
                return {'status': False, 'message': "Batch ID is required"}

        # 2. Call the fetch_batch method to get the batch details
        fetch_data_instance = FetchData()

        # 3. fetch the batch details
        batch_details = fetch_data_instance.fetch_batch_details(batch_id)

        # Check if data was successfully fetched
        if 'error' in batch_details:
            return {'status': False, 'message': batch_details['error']}


        print(batch_details)

        # 4.Save the batch detail to the database
        save_batch_to_database(batch_details)

        return {'status': True, 'message': "Notification received"}
        
    except Exception as e:
        frappe.log_error(message=str(e), title="Batch Notification Error")
        return {'status': False, 'message': f"An error occurred: {str(e)}"}

def save_batch_to_database(batch_data):
    '''
    Save the batch data into the database after fetching it from the API.
    '''
    try:

        for batch in batch_data:
            # Create a new document instance of the Batch Detail DocType
            batch_doc = frappe.get_doc({
                'doctype': 'Batch Detail',  # Replace with your actual DocType name
                'batch_id': batch.get('id'),
                'master_id': batch.get('master_id'),
                'item': batch.get('Item'),
                'weight': batch.get('Weight'),
                'user': batch.get('user'),
                'collections': batch.get('Collections')
            })

            # Insert the document into the database
            batch_doc.insert()

        # Commit changes to the database
        frappe.db.commit()  

        print("Batch details saved successfully.")
        
    except Exception as e:
        print(f"Error saving batch details: {str(e)}")


