import mysql.connector
from contextlib import contextmanager
from mysql.connector import Error

class Database:
    """Class to handle mysql database connections and queries."""

    def __init__(self):
        self.config = {
            'host': 'localhost',  
            'port': 3307,  # Default MySQL port
            'user': 'root',
            'password' : 'root@123',
            'database' : 'Bash_db',
            'raise_on_warnings' : True
        }

    @contextmanager
    def get_connection(self):
        """Context manager for database connection."""

        connect = None
        try:
            print("Attempting DB connection with config:", self.config)
            connect = mysql.connector.connect(**self.config)
            yield connect  #Only reached if connection is succesful

        except Error as e:
            print(f"Database error: {e}")
            raise   #Re-raise the error so that the context manager fails correctly
        
        finally:
            if connect and connect.is_connected():
                connect.close()

    
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