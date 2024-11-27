import frappe, requests


@frappe.whitelist(allow_guest=True)
def receive_notification(*args, **kwargs):
    '''
    Method that receives a notification
    '''
    print(kwargs)

    # 1.Extract batch_id from kwargs
    batch_id = kwargs['batch_id']


    return {'status': True, 'message': "Notification received"}


def save_batch_to_database(batch_data):
    '''
    Save the batch data into the database after fetching it from the API.
    '''
    try:

        # current_user = frappe.session.user
        # print(f"Current User: {current_user}")


        # if current_user == "Guest":
        #     raise PermissionError("Guest users do not have permission to save batch details.")
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


