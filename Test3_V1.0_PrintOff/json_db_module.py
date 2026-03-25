import json
import sqlite3

def connect_db():
    """Connect to the SQLite database."""
    conn = sqlite3.connect('nvr_dvr_bacs_integration.db')  # Update the database name here
    cursor = conn.cursor()
    return conn, cursor

def check_incoming_json(incoming_json):
    """Check if the incoming JSON (object or array of objects) has the same keys as any stored JSON."""
    try:
        # Load the incoming JSON string into a Python dictionary or list
        incoming_json_obj = json.loads(incoming_json)
        
        # Handle both JSON object and array of JSON objects
        if isinstance(incoming_json_obj, dict):
            incoming_json_obj = [incoming_json_obj]  # Convert single object to a list of one object
        
    except ValueError as e:
        print("Invalid incoming JSON format: {}".format(e))
        return False  # Return False if incoming JSON is invalid

    # Get the set of keys from the incoming JSON
    incoming_json_keys_list = [set(obj.keys()) for obj in incoming_json_obj]

    # Connect to the database and fetch all stored JSON configurations
    conn, cursor = connect_db()
    cursor.execute("SELECT json_string FROM json_configurations")
    stored_jsons = cursor.fetchall()
    conn.close()

    # Iterate over stored JSON strings and compare their keys with incoming JSON keys
    for stored_json in stored_jsons:
        try:
            # Load each stored JSON string into a Python dictionary or list
            stored_json_obj = json.loads(stored_json[0])

            # Handle both JSON object and array of JSON objects
            if isinstance(stored_json_obj, dict):
                stored_json_obj = [stored_json_obj]  # Convert single object to list of one object

            stored_json_keys_list = [set(obj.keys()) for obj in stored_json_obj]

            # Compare the keys of the incoming JSON with each stored JSON
            for incoming_keys in incoming_json_keys_list:
                for stored_keys in stored_json_keys_list:
                    if incoming_keys == stored_keys:
                        print("Match found with stored JSON keys: {}".format(stored_json[0]))
                        return True  # Return True if any key set matches
            
        except ValueError as e:
            print("Invalid stored JSON format in database: {}".format(e))

    print("No matching JSON configuration found based on keys.")
    return False  # Return False if no match based on keys is found
