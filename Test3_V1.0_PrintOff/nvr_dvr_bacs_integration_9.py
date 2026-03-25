import json
import sqlite3
import sys  # For exiting the program

def connect_db():
    """Connect to the SQLite database."""
    conn = sqlite3.connect('nvr_dvr_bacs_integration.db')  # Update the database name here
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS json_configurations (id INTEGER PRIMARY KEY, json_string TEXT)''')
    return conn, cursor

def add_json_to_db():
    """Add a JSON configuration to the database."""
    print("Enter JSON configuration to add (press Enter twice to finish):")
    
    json_lines = []
    
    # Capture input until the user presses Enter twice
    while True:
        line = raw_input()  # Read a line (Python 2)
        if line == "":  # If an empty line is detected, break the loop
            break
        json_lines.append(line)  # Collect all lines including leading/trailing spaces

    # Join the collected lines into a single JSON string
    json_str = "\n".join(json_lines).strip()

    # Debugging: Show what was captured
    print("Captured JSON string: {}".format(json_str))

    # Validate if the string is valid JSON (can be an object or an array of objects)
    try:
        json_obj = json.loads(json_str)  # This will raise a ValueError if it's not valid JSON
        print("Valid JSON format.")
    except ValueError as e:
        print("Invalid JSON format: {}".format(e))
        return

    # If the JSON is valid, proceed to store it in the database
    conn, cursor = connect_db()
    cursor.execute("INSERT INTO json_configurations (json_string) VALUES (?)", (json_str,))
    conn.commit()
    conn.close()
    print("JSON configuration added to the database.")

def delete_json_from_db(json_id):
    """Delete a JSON configuration from the database by its ID."""
    conn, cursor = connect_db()
    cursor.execute("DELETE FROM json_configurations WHERE id=?", (json_id,))
    conn.commit()
    conn.close()
    print("JSON configuration with ID {} deleted from the database.".format(json_id))

def view_json_in_db():
    """View all JSON configurations stored in the database."""
    conn, cursor = connect_db()
    cursor.execute("SELECT id, json_string FROM json_configurations")
    records = cursor.fetchall()
    conn.close()
    if records:
        for record in records:
            print("ID: {}, JSON: {}".format(record[0], record[1]))

def get_multiline_input(prompt):
    """Helper function to capture multiline input for JSON."""
    print(prompt)
    json_lines = []
    
    while True:
        line = raw_input()  # Read a line
        if line == "":
            break
        json_lines.append(line)

    json_str = "\n".join(json_lines).strip()
    return json_str

def check_incoming_json(incoming_json):
    """Check if the incoming JSON has the same keys as any JSON stored in the database."""
    try:
        # Load the incoming JSON string (can be an object or an array of objects)
        incoming_json_obj = json.loads(incoming_json)
        if isinstance(incoming_json_obj, dict):  # Single JSON object
            incoming_json_obj = [incoming_json_obj]  # Treat it as a list of one object
    except ValueError as e:
        print("Invalid incoming JSON format: {}".format(e))
        return False  # Return False if incoming JSON is invalid

    # Connect to the database and fetch all stored JSON configurations
    conn, cursor = connect_db()
    cursor.execute("SELECT json_string FROM json_configurations")
    stored_jsons = cursor.fetchall()
    conn.close()

    # Iterate over stored JSON strings
    for stored_json in stored_jsons:
        try:
            # Load each stored JSON string (can be an object or an array of objects)
            stored_json_obj = json.loads(stored_json[0])
            if isinstance(stored_json_obj, dict):  # Single JSON object
                stored_json_obj = [stored_json_obj]  # Treat it as a list of one object

            # Compare each object in the incoming JSON with the objects stored in the database
            for incoming_obj in incoming_json_obj:
                incoming_json_keys = set(incoming_obj.keys())
                
                for stored_obj in stored_json_obj:
                    stored_json_keys = set(stored_obj.keys())
                    # Compare keys (ignore values)
                    if incoming_json_keys == stored_json_keys:
                        print("Match found with stored JSON keys: {}".format(stored_json[0]))
                        return True  # Return True if keys match
        except ValueError as e:
            print("Invalid stored JSON format in database: {}".format(e))

    print("No matching JSON configuration found based on keys.")
    return False  # Return False if no match based on keys is found

def main():
    while True:
        print("Choose an option:")
        print("1. Add JSON configuration to database")
        print("2. Delete JSON configuration from database")
        print("3. View JSON configurations in database")
        print("4. Check incoming JSON against stored JSON configurations")
        print("5. Exit")
        choice = raw_input("Enter your choice: ")
        
        if choice == '1':
            add_json_to_db()
        elif choice == '2':
            json_id = raw_input("Enter the ID of the JSON configuration to delete: ")
            delete_json_from_db(int(json_id))
        elif choice == '3':
            view_json_in_db()
        elif choice == '4':
            incoming_json = get_multiline_input("Enter incoming JSON string (press Enter twice to finish):")
            is_matched = check_incoming_json(incoming_json)
            if is_matched:
                print("Action based on JSON match can be performed here.")
            else:
                print("No action taken as no match was found.")
        elif choice == '5':
            print("Exiting the program.")
            sys.exit(0)  # Exit the program
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
