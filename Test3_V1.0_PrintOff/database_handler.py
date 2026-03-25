import sqlite3
import logging

class DatabaseHandler:
    """
    A class to handle SQLite database operations for storing and managing JSON payloads.

    Attributes:
        db_name (str): The name of the database file.
        conn (sqlite3.Connection): The SQLite database connection object.

    Methods:
        connect(): Establishes a connection to the SQLite database.
        create_table(): Creates the json_data table if it does not exist.
        insert_json(json_str): Inserts a JSON string into the json_data table with a status of 'pending'.
        is_child_ready(): Checks if there are any pending JSON entries in the table.
        get_json_string(): Retrieves the first pending JSON string from the table.
        mark_as_sent(row_id): Marks a specific entry as 'sent'.
        mark_as_failed(row_id): Marks a specific entry as 'failed'.
        reset_status(row_id): Resets the status of a specific entry to 'pending'.
        close(): Closes the database connection.
    """

    def __init__(self, db_name='payloads.db'):
        """
        Initializes the DatabaseHandler with the given database name and ensures the table is created.

        Args:
            db_name (str): The name of the database file. Defaults to 'payloads.db'.
        """
        self.db_name = db_name
        self.conn = None
        self.connect()
        self.create_table()

    def connect(self):
        """
        Establishes a connection to the SQLite database.

        Raises:
            sqlite3.Error: If there is an error connecting to the database.
        """
        try:
            self.conn = sqlite3.connect(self.db_name)
        except sqlite3.Error as e:
            logging.error(u"Error connecting to database: {}".format(e))
            raise
            pass
        except sqlite3.OperationalError as e:
            logging.error("OperationalError: %s" % e)
            raise  # Re-raise the OperationalError after logging
            # Handle specific operational error cases here if needed
            pass
    def create_table(self):
        """
        Creates the json_data table if it does not exist.

        Raises:
            sqlite3.Error: If there is an error creating the table.
        """
        try:
            with self.conn:
                self.conn.execute(u'''
                    CREATE TABLE IF NOT EXISTS json_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        json_str TEXT NOT NULL,
                        status TEXT NOT NULL DEFAULT "pending"
                    )
                ''')
        except sqlite3.Error as e:
            logging.error(u"Error creating table: {}".format(e))
            raise
            pass
        except sqlite3.OperationalError as e:
            logging.error("OperationalError: %s" % e)
            raise  # Re-raise the OperationalError after logging
            # Handle specific operational error cases here if needed
            pass

    def insert_json(self, json_str):
        """
        Inserts a JSON string into the json_data table with a status of 'pending'.

        Args:
            json_str (str): The JSON string to be inserted.

        Raises:
            sqlite3.Error: If there is an error inserting the JSON string.
        """
        try:
            with self.conn:
                self.conn.execute(
                    u'INSERT INTO json_data (json_str, status) VALUES (?, ?)',
                    (json_str, 'pending')
                )
        except sqlite3.Error as e:
            logging.error(u"Error inserting JSON: {}".format(e))
            raise
            pass
        except sqlite3.OperationalError as e:
            logging.error("OperationalError: %s" % e)
            raise  # Re-raise the OperationalError after logging
            # Handle specific operational error cases here if needed
            pass
    def is_child_ready(self):
        """
        Checks if there are any pending JSON entries in the table.

        Returns:
            bool: True if no pending entries exist, False otherwise.

        Raises:
            sqlite3.Error: If there is an error executing the query.
        """
        try:
            cursor = self.conn.execute(u'SELECT id FROM json_data WHERE status = ?', ('pending',))
            row = cursor.fetchone()
            return row is None
        except sqlite3.Error as e:
            logging.error(u"Error checking if child is ready: {}".format(e))
            raise
            pass
        except sqlite3.OperationalError as e:
            logging.error("OperationalError: %s" % e)
            raise  # Re-raise the OperationalError after logging
            # Handle specific operational error cases here if needed
            pass
    def get_json_string(self):
        """
        Retrieves the first pending JSON string from the table.

        Returns:
            tuple: A tuple containing the row ID and the JSON string. Returns (None, None) if no pending entries exist.

        Raises:
            sqlite3.Error: If there is an error executing the query.
        """
        try:
            cursor = self.conn.execute(u'SELECT id, json_str FROM json_data WHERE status = ?', ('pending',))
            row = cursor.fetchone()
            if row:
                return row[0], row[1]
            return None, None
        except sqlite3.Error as e:
            logging.error(u"Error retrieving JSON string: {}".format(e))
            raise
            pass
        except sqlite3.OperationalError as e:
            logging.error("OperationalError: %s" % e)
            raise  # Re-raise the OperationalError after logging
            # Handle specific operational error cases here if needed
            pass
    def mark_as_sent(self, row_id):
        """
        Marks a specific entry as 'sent'.

        Args:
            row_id (int): The ID of the row to update.

        Raises:
            sqlite3.Error: If there is an error updating the row.
        """
        try:
            with self.conn:
                self.conn.execute(u'UPDATE json_data SET status = ? WHERE id = ?', ('sent', row_id))
        except sqlite3.Error as e:
            logging.error(u"Error marking as sent: {}".format(e))
            raise
            pass
        except sqlite3.OperationalError as e:
            logging.error("OperationalError: %s" % e)
            raise  # Re-raise the OperationalError after logging
            # Handle specific operational error cases here if needed
            pass
    def mark_as_failed(self, row_id):
        """
        Marks a specific entry as 'failed'.

        Args:
            row_id (int): The ID of the row to update.

        Raises:
            sqlite3.Error: If there is an error updating the row.
        """
        try:
            with self.conn:
                self.conn.execute(u'UPDATE json_data SET status = ? WHERE id = ?', ('failed', row_id))
        except sqlite3.Error as e:
            logging.error(u"Error marking as failed: {}".format(e))
            raise
            pass
        except sqlite3.OperationalError as e:
            logging.error("OperationalError: %s" % e)
            raise  # Re-raise the OperationalError after logging
            # Handle specific operational error cases here if needed
            pass
    def reset_status(self, row_id):
        """
        Resets the status of a specific entry to 'pending'.

        Args:
            row_id (int): The ID of the row to update.

        Raises:
            sqlite3.Error: If there is an error updating the row.
        """
        try:
            with self.conn:
                self.conn.execute(u'UPDATE json_data SET status = ? WHERE id = ?', ('pending', row_id))
        except sqlite3.Error as e:
            logging.error(u"Error resetting status: {}".format(e))
            raise
            pass
        except sqlite3.OperationalError as e:
            logging.error("OperationalError: %s" % e)
            raise  # Re-raise the OperationalError after logging
            # Handle specific operational error cases here if needed
            pass
    def close(self):
        """
        Closes the database connection.
        """
        if self.conn:
            self.conn.close()





#import sqlite3
#import logging
import time

class DatabaseHandlerOperationalError:
    """
    A class to handle SQLite database operations for storing and managing JSON payloads.

    Attributes:
        db_name (str): The name of the database file.
        conn (sqlite3.Connection): The SQLite database connection object.

    Methods:
        connect(): Establishes a connection to the SQLite database.
        create_table(): Creates the json_data table if it does not exist.
        insert_json(json_str): Inserts a JSON string into the json_data table with a status of 'pending'.
        is_child_ready(): Checks if there are any pending JSON entries in the table.
        get_json_string(): Retrieves the first pending JSON string from the table.
        mark_as_sent(row_id): Marks a specific entry as 'sent'.
        mark_as_failed(row_id): Marks a specific entry as 'failed'.
        reset_status(row_id): Resets the status of a specific entry to 'pending'.
        close(): Closes the database connection.
    """

    def __init__(self, db_name='payloads.db'):
        """
        Initializes the DatabaseHandler with the given database name and ensures the table is created.

        Args:
            db_name (str): The name of the database file. Defaults to 'payloads.db'.
        """
        self.db_name = db_name
        self.conn = None
        self.connect()
        self.create_table()

    def connect(self):
        """
        Establishes a connection to the SQLite database and sets WAL mode.

        Raises:
            sqlite3.Error: If there is an error connecting to the database.
        """
        try:
            self.conn = sqlite3.connect(self.db_name, timeout=30)  # Adjust timeout as needed
            self.conn.execute('PRAGMA journal_mode=WAL;')
        except sqlite3.Error as e:
            logging.error(u"Error connecting to database: {}".format(e))
            raise

    def create_table(self):
        """
        Creates the json_data table if it does not exist.

        Raises:
            sqlite3.Error: If there is an error creating the table.
        """
        try:
            with self.conn:
                self.connect()
                self.conn.execute(u'''
                    CREATE TABLE IF NOT EXISTS json_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        json_str TEXT NOT NULL,
                        status TEXT NOT NULL DEFAULT "pending"
                    )
                ''')
        except sqlite3.Error as e:
            logging.error(u"Error creating table: {}".format(e))
            raise

    def insert_json(self, json_str):
        """
        Inserts a JSON string into the json_data table with a status of 'pending'.

        Args:
            json_str (str): The JSON string to be inserted.

        Raises:
            sqlite3.Error: If there is an error inserting the JSON string.
        """
        try:
            with self.conn:
                self.connect()
                self.conn.execute(
                    u'INSERT INTO json_data (json_str, status) VALUES (?, ?)',
                    (json_str, 'pending')
                )
        except sqlite3.Error as e:
            logging.error(u"Error inserting JSON: {}".format(e))
            raise

    def is_child_ready(self, retry_count=5, retry_delay=1):
        """
        Checks if there are any pending JSON entries in the table.

        Args:
            retry_count (int): The number of times to retry the operation if the database is locked.
            retry_delay (int): The delay between retries in seconds.

        Returns:
            bool: True if no pending entries exist, False otherwise.

        Raises:
            sqlite3.Error: If there is an error executing the query.
        """
        for attempt in range(retry_count):
            try:
                self.connect()
                cursor = self.conn.execute(u'SELECT id FROM json_data WHERE status = ?', ('pending',))
                row = cursor.fetchone()
                return row is None
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e):
                    logging.warning(u"Database is locked. Retrying in {} seconds... (attempt {}/{})".format(retry_delay, attempt + 1, retry_count))
                    time.sleep(retry_delay)
                else:
                    logging.error(u"Error checking if child is ready: {}".format(e))
                    raise
        logging.error(u"Failed to check if child is ready after {} attempts".format(retry_count))
        raise sqlite3.OperationalError("Database is locked after {} attempts".format(retry_count))

    def get_json_string(self, retry_count=5, retry_delay=1):
        """
        Retrieves the first pending JSON string from the table.

        Args:
            retry_count (int): The number of times to retry the operation if the database is locked.
            retry_delay (int): The delay between retries in seconds.

        Returns:
            tuple: A tuple containing the row ID and the JSON string. Returns (None, None) if no pending entries exist.

        Raises:
            sqlite3.Error: If there is an error executing the query.
        """
        for attempt in range(retry_count):
            try:
                self.connect()
                cursor = self.conn.execute(u'SELECT id, json_str FROM json_data WHERE status = ?', ('pending',))
                row = cursor.fetchone()
                if row:
                    return row[0], row[1]
                return None, None
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e):
                    logging.warning(u"Database is locked. Retrying in {} seconds... (attempt {}/{})".format(retry_delay, attempt + 1, retry_count))
                    time.sleep(retry_delay)
                else:
                    logging.error(u"Error retrieving JSON string: {}".format(e))
                    raise
        logging.error(u"Failed to retrieve JSON string after {} attempts".format(retry_count))
        raise sqlite3.OperationalError("Database is locked after {} attempts".format(retry_count))

    def mark_as_sent(self, row_id, retry_count=5, retry_delay=1):
        """
        Marks a specific entry as 'sent'.

        Args:
            row_id (int): The ID of the row to update.
            retry_count (int): The number of times to retry the operation if the database is locked.
            retry_delay (int): The delay between retries in seconds.

        Raises:
            sqlite3.Error: If there is an error updating the row.
        """
        for attempt in range(retry_count):
            try:
                with self.conn:
                    self.connect()
                    self.conn.execute(u'UPDATE json_data SET status = ? WHERE id = ?', ('sent', row_id))
                return
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e):
                    logging.warning(u"Database is locked. Retrying in {} seconds... (attempt {}/{})".format(retry_delay, attempt + 1, retry_count))
                    time.sleep(retry_delay)
                else:
                    logging.error(u"Error marking as sent: {}".format(e))
                    raise
        logging.error(u"Failed to mark as sent after {} attempts".format(retry_count))
        raise sqlite3.OperationalError("Database is locked after {} attempts".format(retry_count))

    def mark_as_failed(self, row_id, retry_count=5, retry_delay=1):
        """
        Marks a specific entry as 'failed'.

        Args:
            row_id (int): The ID of the row to update.
            retry_count (int): The number of times to retry the operation if the database is locked.
            retry_delay (int): The delay between retries in seconds.

        Raises:
            sqlite3.Error: If there is an error updating the row.
        """
        for attempt in range(retry_count):
            try:
                with self.conn:
                    self.connect()
                    self.conn.execute(u'UPDATE json_data SET status = ? WHERE id = ?', ('failed', row_id))
                return
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e):
                    logging.warning(u"Database is locked. Retrying in {} seconds... (attempt {}/{})".format(retry_delay, attempt + 1, retry_count))
                    time.sleep(retry_delay)
                else:
                    logging.error(u"Error marking as failed: {}".format(e))
                    raise
        logging.error(u"Failed to mark as failed after {} attempts".format(retry_count))
        raise sqlite3.OperationalError("Database is locked after {} attempts".format(retry_count))

    def reset_status(self, row_id, retry_count=5, retry_delay=1):
        """
        Resets the status of a specific entry to 'pending'.

        Args:
            row_id (int): The ID of the row to update.
            retry_count (int): The number of times to retry the operation if the database is locked.
            retry_delay (int): The delay between retries in seconds.

        Raises:
            sqlite3.Error: If there is an error updating the row.
        """
        for attempt in range(retry_count):
            try:
                with self.conn:
                    self.connect()
                    self.conn.execute(u'UPDATE json_data SET status = ? WHERE id = ?', ('pending', row_id))
                return
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e):
                    logging.warning(u"Database is locked. Retrying in {} seconds... (attempt {}/{})".format(retry_delay, attempt + 1, retry_count))
                    time.sleep(retry_delay)
                else:
                    logging.error(u"Error resetting status: {}".format(e))
                    raise
        logging.error(u"Failed to reset status after {} attempts".format(retry_count))
        raise sqlite3.OperationalError("Database is locked after {} attempts".format(retry_count))

    def close(self):
        """
        Closes the database connection.
        """
        if self.conn:
            self.conn.close()


#import sqlite3
import logging
import time
import os
import shutil

class DatabaseHandlerOperationalErrorDatabaseClose:
    """
    A class to handle SQLite database operations for storing and managing JSON payloads.
    """

    def __init__(self, db_name='payloads.db'):
        self.db_name = db_name
        self.conn = None
        self.connect()
        self.create_table()

    def connect(self):
        """
        Establishes a connection to the SQLite database and sets WAL mode.
        """
        try:
            self.conn = sqlite3.connect(self.db_name, timeout=30)
            self.conn.execute('PRAGMA journal_mode=WAL;')
        except sqlite3.Error as e:
            logging.error(u"Error connecting to database: {}".format(e))
            raise

    def create_table(self):
        """
        Creates the json_data table if it does not exist.
        """
        try:
            with self.conn:
                self.connect()
                self.conn.execute(u'''
                    CREATE TABLE IF NOT EXISTS json_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        json_str TEXT NOT NULL,
                        status TEXT NOT NULL DEFAULT "pending"
                    )
                ''')
        except sqlite3.Error as e:
            logging.error(u"Error creating table: {}".format(e))
            raise
        finally:
                self.close()                
    def insert_json(self, json_str):
        """
        Inserts a JSON string into the json_data table with a status of 'pending'.
        """
        try:
            with self.conn:
                self.connect()
                self.conn.execute(
                    u'INSERT INTO json_data (json_str, status) VALUES (?, ?)',
                    (json_str, 'pending')
                )
        except sqlite3.Error as e:
            logging.error(u"Error inserting JSON: {}".format(e))
            raise

    def is_child_ready(self, retry_count=5, retry_delay=1):
        """
        Checks if there are any pending JSON entries in the table.
        """
        for attempt in range(retry_count):
            try:
                self.connect()
                cursor = self.conn.execute(u'SELECT id FROM json_data WHERE status = ?', ('pending',))
                row = cursor.fetchone()
                return row is None
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e):
                    logging.warning(u"Database is locked. Retrying in {} seconds... (attempt {}/{})".format(retry_delay, attempt + 1, retry_count))
                    time.sleep(retry_delay)
                else:
                    logging.error(u"Error checking if child is ready: {}".format(e))
                    raise
            finally:
                self.close()                                
        logging.error(u"Failed to check if child is ready after {} attempts".format(retry_count))
        raise sqlite3.OperationalError("Database is locked after {} attempts".format(retry_count))

    def get_json_string(self, retry_count=5, retry_delay=1):
        """
        Retrieves the first pending JSON string from the table.
        """
        for attempt in range(retry_count):
            try:
                self.connect()
                cursor = self.conn.execute(u'SELECT id, json_str FROM json_data WHERE status = ?', ('pending',))
                row = cursor.fetchone()
                if row:
                    return row[0], row[1]
                return None, None
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e):
                    logging.warning(u"Database is locked. Retrying in {} seconds... (attempt {}/{})".format(retry_delay, attempt + 1, retry_count))
                    time.sleep(retry_delay)
                else:
                    logging.error(u"Error retrieving JSON string: {}".format(e))
                    raise
            finally:
                self.close()                                
        logging.error(u"Failed to retrieve JSON string after {} attempts".format(retry_count))
        raise sqlite3.OperationalError("Database is locked after {} attempts".format(retry_count))

    def mark_as_sent(self, row_id, retry_count=5, retry_delay=1):
        """
        Marks a specific entry as 'sent'.
        """
        for attempt in range(retry_count):
            try:
                with self.conn:
                    self.connect()
                    self.conn.execute(u'UPDATE json_data SET status = ? WHERE id = ?', ('sent', row_id))
                return
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e):
                    logging.warning(u"Database is locked. Retrying in {} seconds... (attempt {}/{})".format(retry_delay, attempt + 1, retry_count))
                    time.sleep(retry_delay)
                else:
                    logging.error(u"Error marking as sent: {}".format(e))
                    raise
            finally:
                self.close()                                
        logging.error(u"Failed to mark as sent after {} attempts".format(retry_count))
        raise sqlite3.OperationalError("Database is locked after {} attempts".format(retry_count))

    def mark_as_failed(self, row_id, retry_count=5, retry_delay=1):
        """
        Marks a specific entry as 'failed'.
        """
        for attempt in range(retry_count):
            try:
                with self.conn:
                    self.connect()
                    self.conn.execute(u'UPDATE json_data SET status = ? WHERE id = ?', ('failed', row_id))
                return
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e):
                    logging.warning(u"Database is locked. Retrying in {} seconds... (attempt {}/{})".format(retry_delay, attempt + 1, retry_count))
                    time.sleep(retry_delay)
                else:
                    logging.error(u"Error marking as failed: {}".format(e))
                    raise
            finally:
                self.close()                                
        logging.error(u"Failed to mark as failed after {} attempts".format(retry_count))
        raise sqlite3.OperationalError("Database is locked after {} attempts".format(retry_count))

    def reset_status(self, row_id, retry_count=5, retry_delay=1):
        """
        Resets the status of a specific entry to 'pending'.
        """
        for attempt in range(retry_count):
            try:
                with self.conn:
                    self.connect()
                    self.conn.execute(u'UPDATE json_data SET status = ? WHERE id = ?', ('pending', row_id))
                return
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e):
                    logging.warning(u"Database is locked. Retrying in {} seconds... (attempt {}/{})".format(retry_delay, attempt + 1, retry_count))
                    time.sleep(retry_delay)
                else:
                    logging.error(u"Error resetting status: {}".format(e))
                    raise
            finally:
                self.close()                
        logging.error(u"Failed to reset status after {} attempts".format(retry_count))
        raise sqlite3.OperationalError("Database is locked after {} attempts".format(retry_count))

    def backup_database(self, backup_name='payloads_backup.db'):
        """
        Creates a backup of the current database.

        Args:
            backup_name (str): The name of the backup file.
        """
        try:
            if os.path.exists(self.db_name):
                shutil.copyfile(self.db_name, backup_name)
                logging.info(u"Database backup created: {}".format(backup_name))
        except Exception as e:
            logging.error(u"Error creating database backup: {}".format(e))
            raise

    def restore_database(self, backup_name='payloads_backup.db'):
        """
        Restores the database from a backup file.

        Args:
            backup_name (str): The name of the backup file to restore from.
        """
        try:
            if os.path.exists(backup_name):
                self.close()
                shutil.copyfile(backup_name, self.db_name)
                self.connect()
                logging.info(u"Database restored from backup: {}".format(backup_name))
        except Exception as e:
            logging.error(u"Error restoring database: {}".format(e))
            raise

    def close(self):
        """
        Closes the database connection.
        """
        if self.conn:
            self.conn.close()


