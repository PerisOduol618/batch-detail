import frappe, requests

class FetchData:
    '''
    Define a class to interact with the accounting API and fetch data
    '''

    def __init__(self):
        self.base_url = 'http://65.21.156.159'
        self.batch_details_uri = '/api/accounting/batchdetails/'
        self.auth_token = f"{api_key}:{api_secret}"

    def get_request(self, url, headers=None):
        std_headers = {
            "Authorization": f"token {self.auth_token}",
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

            # Transform the flat list to a nested structure
            grouped_data = {}
            for item in data:
                master_id = item.get('master_id')
                if master_id not in grouped_data:
                    grouped_data[master_id] = {
                        'master_id': master_id,
                        'batch_id': item.get('id'),
                        'sacks': []
                    }
                grouped_data[master_id]['sacks'].append({
                    'sack_id': item.get('id'),
                    'item': item.get('Item'),
                    'weight': item.get('Weight'),
                    'user': item.get('user'),
                    'time': item.get('time'),
                    'collections': item.get('Collections')
                })

            # Convert the grouped data back to a list
            return list(grouped_data.values())

        else:
            return {"error": f"Unable to fetch batch details (status code: {response.status_code})"}
        

@frappe.whitelist(allow_guest=True)
def receive_notification(*args, **kwargs):
    '''
    Method that receives a notification and processes it.
    '''
    try:
        batch_id = kwargs.get('batch_id')
        if not batch_id:
            return {'status': False, 'message': "Batch ID is required"}

        # Fetch batch details from API
        fetch_data_instance = FetchData()
        batch_details = fetch_data_instance.fetch_batch_details(batch_id)

        if isinstance(batch_details, dict) and 'error' in batch_details:
            return {'status': False, 'message': batch_details['error']}

        # Save batch details to the database
        save_batch_to_database(batch_details)

        return {'status': True, 'message': "Batch details saved successfully."}

    except Exception as e:
        frappe.log_error(message=str(e), title="Batch Notification Error")
        return {'status': False, 'message': f"An error occurred: {str(e)}"}

def save_batch_to_database(batch_data):
    '''
    Save the batch data into the database after fetching it from the API.
    '''
    try:
        for batch in batch_data:
            # Fetch or create the parent batch document
            batch_doc = get_or_create_batch(batch)
            print(batch_doc)


            # Add sacks as child rows
            add_sacks_to_batch(batch_doc, batch.get('sacks', []))

        # Commit changes to the database
        frappe.db.commit()
        print("Batch details and sacks saved successfully.")

    except Exception as e:
        frappe.log_error(message=str(e), title="Save Batch Details Error")
        raise e 

def get_or_create_batch(batch):
    '''
    Fetch an existing batch or create a new one.
    '''
    existing_batch = frappe.get_all(
        'Batch Detail', 
        filters={'batch_id': batch.get('batch_id')}, 
        fields=['name']
    )
    if existing_batch:
        return frappe.get_doc('Batch Detail', existing_batch[0]['name'])

    batch_doc = frappe.get_doc({
        'doctype': 'Batch Detail',
        'batch_id': batch.get('batch_id'),
        'master_id': batch.get('master_id')
    })
   
    batch_doc.insert()
    return batch_doc

def add_sacks_to_batch(batch_doc, sacks):
    '''
    Add sacks to the batch's child table.
    '''
    for sack in sacks:
        # To Avoid duplication: Check if sack already exists
        existing_sack = frappe.get_all(
            'Sack', 
            filters={'parent': batch_doc.name, 'sack_id': sack.get('sack_id')}, 
            fields=['name']
        )
        if not existing_sack:
            sack_doc = batch_doc.append('sacks', {
                'sack_id': sack.get('sack_id'),
                'item': sack.get('item'),
                'weight': sack.get('weight'),
                'user': sack.get('user'),
                'time': sack.get('time'),
                'collections': sack.get('collections')
            })
    batch_doc.save()

