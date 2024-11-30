import frappe, requests

class FetchData:
    '''
    Define a class to interact with the accounting API and fetch data
    '''

    def __init__(self):
        self.base_url = 'http://65.21.156.159'
        self.batch_details_uri = '/api/accounting/batchdetails/'

    def get_request(self, url, headers=None):
        std_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if not headers:
            headers = std_headers

        response = requests.get(url, headers=headers)
        return response
    
    def fetch_batch_details(self, batch_id):
        url = f"{self.base_url}{self.batch_details_uri}{batch_id}"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict):
                data = [data]
            return data
        else:
            return {"error": f"Unable to fetch batch details (status code: {response.status_code})"}

@frappe.whitelist(allow_guest=True)
def receive_notification(*args, **kwargs):
    '''
    Method that receives a notification and processes it.
    '''
    print(kwargs)
    try:
        # 1. Extract batch_id from kwargs
        batch_id = kwargs['batch_id']
        
        
        if not batch_id:
            return {'status': False, 'message': "Batch ID is required"}

        # 2. Call the fetch_batch method to get the batch details using batch_id
        fetch_data_instance = FetchData()
        batch_details = fetch_data_instance.fetch_batch_details(batch_id)

        # Check if data was successfully fetched
        if 'error' in batch_details:
            return {'status': False, 'message': batch_details['error']}

        print(batch_details)

        # 3. Save the batch details into the database
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
            # 1. Check if the parent document exists
            existing_batch = frappe.get_all(
                'Batch Detail',  # Parent Doctype
                filters={'batch_id': batch.get('id')}, 
                fields=['name']  # Only retrieve the name field (ID of the document)
            )

            # 2. If Batch Detail exists, get the first document; else, create a new document
            if existing_batch:
                batch_doc = frappe.get_doc('Batch Detail', existing_batch[0]['name'])
            else:
                batch_doc = frappe.get_doc({
                    'doctype': 'Batch Detail', 
                    'batch_id': batch.get('id'),  # The unique batch ID
                    'master_id': batch.get('master_id') 
                })
                batch_doc.insert()


            # 3. For each sack (child document), create and insert them as rows in the child table
            for sack in batch.get('sacks', []):
                sack_doc = frappe.get_doc({
                    'doctype': 'Sack',  
                    'parent': batch_doc.name,  # Link to the parent Batch Detail
                    'sack_id': sack.get('id'),
                    'item': sack.get('Item'),
                    'weight': sack.get('Weight'),
                    'user': sack.get('user'),
                    'time': sack.get('time'),
                    'collections': sack.get('Collections')
                })

                sack_doc.insert()

        # 4. Commit changes to the database
        frappe.db.commit()
        print("Batch details saved successfully.")
        
    except Exception as e:
        print(f"Error saving batch details: {str(e)}")
