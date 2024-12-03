import frappe
import requests

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

            # Transform the flat list to a nested structure
            grouped_data = {}
            for item in data:
                master_id = item.get('master_id')
                if master_id not in grouped_data:
                    grouped_data[master_id] = {
                        'master_id': master_id,
                        'batch_id': item.get('id'),
                        'batch_items': []
                    }
                grouped_data[master_id]['batch_items'].append({
                    'item_id': item.get('id'),
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
        print(batch_id)

       
        if not batch_id:
            return {'status': False, 'message': "Batch ID is required"}

        # Fetch batch details from API
        fetch_data_instance = FetchData()
        batch_details = fetch_data_instance.fetch_batch_details(batch_id)

        if isinstance(batch_details, dict) and 'error' in batch_details:
            return {'status': False, 'message': batch_details['error']}

        # Save batch and batch items to the database
        save_batch_and_items(batch_details)

        return {'status': True, 'message': "Batch details and items saved successfully."}

    except Exception as e:
        frappe.log_error(message=str(e), title="Batch Notification Error")
        return {'status': False, 'message': f"An error occurred: {str(e)}"}

def save_batch_and_items(batch_data):
    '''
    Save the batch and its batch items into the database.
    '''
    try:
        for batch in batch_data:
            # Get or create the parent batch document
            batch_doc = get_or_create_batch(batch)
            
            # Ensure batch_items exists and is a list
            batch_items = batch.get('batch_items', [])
            
            if not batch_items:
                raise ValueError(f"No batch items found for batch_id: {batch.get('batch_id')}")
            
            # Add batch items to batch
            add_batch_items_to_batch(batch_doc, batch_items)
        
        # Commit changes to the database
        frappe.db.commit()
        print("Batch and batch items saved successfully.")
    except Exception as e:
        frappe.log_error(message=str(e), title="Save Batch Error")
        raise e

def get_or_create_batch(batch_data):
    '''
    Fetch or create the parent batch document.
    '''
    try:
        # Attempt to get the batch by batch_id
        existing_batch = frappe.get_all(
            'Batch',  # Parent table name
            filters={'batch_id': batch_data.get('batch_id')},  # Filter by batch_id
            fields=['name']
        )
        
        if existing_batch:
            # If the batch exists, return the existing Batch document
            batch_doc = frappe.get_doc('Batch', existing_batch[0]['name'])
            print(f"Found existing batch: {batch_doc.name}")
        else:
            # If no existing batch, create a new one
            batch_doc = frappe.get_doc({
                'doctype': 'Batch',
                'batch_id': batch_data.get('batch_id'),
                'master_id': batch_data.get('master_id') 
            })
            batch_doc.insert()  # Insert the new batch
            print(f"Created new batch: {batch_doc.name}")
        
        return batch_doc
    except Exception as e:
        frappe.log_error(message=str(e), title="Error fetching or creating batch")
        raise e



def add_batch_items_to_batch(batch_doc, batch_items):
    """
    Add batch items to the batch's batch_details child table only if not already added.
    Prevent duplicate batch saves or creation.
    """
    try:
        # Check if batch already exists
        if not batch_doc:
            raise ValueError("Batch document is missing. Cannot proceed.")

        # Fetch existing items in the batch
        existing_batch_items = batch_doc.get('batch_details', [])
        existing_item_ids = {item.item_id for item in existing_batch_items}

        # Filter out items that already exist in the batch
        new_items = [
            item for item in batch_items
            if item['item_id'] not in existing_item_ids
        ]

        if not new_items:
            print(f"Batch {batch_doc.batch_id} already has all items. No new items to add.")
            return

        # Add new items to the batch_details table
        for item in new_items:
            batch_item = {
                'item_id': item.get('item_id'),
                'item': item.get('item'),
                'weight': item.get('weight'),
                'user': item.get('user'),
                'time': item.get('time'),
                'collections': item.get('collections')
            }
            batch_doc.append('batch_details', batch_item)
            print(f"Added batch item: {batch_item['item_id']} to batch {batch_doc.batch_id}")

        # Save the batch document only if new items were added
        if new_items:
            batch_doc.save()
            print(f"Batch {batch_doc.batch_id} saved with {len(new_items)} new items.")
        else:
            print(f"No new items added to batch {batch_doc.batch_id}. Skip saving.")

    except Exception as e:
        frappe.log_error(message=str(e), title="Error adding batch items")
        raise e
