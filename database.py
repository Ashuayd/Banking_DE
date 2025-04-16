import mysql.connector
from contextlib import contextmanager
from mysql.connector import Error

class Database:
    """Class to handle mysql database connections and queries."""

    def __init__(self):
        self.config = {
            'host': 'localhost',  
            'port': 3306,  # Default MySQL port
            'user': 'root',
            'password' : 'root@123',
            'database' : 'Bash_db',
            'raise_on_warnings' : True
        }
        self.connection = None

    @contextmanager
    def get_connection(self):
        """Context manager for database connection."""

        try:
            self.connection = mysql.connector.connect(**self.config)
            yield self.connection

        except Error as e:
            print(f"Database error: {e}")
        
        finally:
            if self.connection and self.connection.is_connected():
                self.connection.close()
                self.connection = None

    def start_transaction(self):
        """Start a transaction."""
        try:
            self.connection.autocommit = False
            print("Transaction started.")
        except Exception as e:
            print(f"Error starting transaction: {e}")

    def commit_transaction(self):
        """Commit the current transaction."""
        try:
            self.connection.commit()
            print("Transaction committed.")
        except Exception as e:
            print(f"Error committing transaction: {e}")

    def rollback_transaction(self):
        """Rollback the current transaction."""
        try:
            self.connection.rollback()
            print("Transaction rolled back.")
        except Exception as e:
            print(f"Error rolling back transaction: {e}")
   
    def execute_query(self, query,params = None, fetch = False):
        """Execute a query and return results if fetch is True."""
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute(query, params or ())
                if fetch:
                    result = cursor.fetchall()
                    return result
                else:
                    conn.commit()
                    return cursor.rowcount
            
            except Error as e:
                print(f"Query error: {e}")
                return None
            finally:
                cursor.close()