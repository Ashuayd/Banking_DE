import os
from google.cloud.sql.connector import Connector, IPTypes
import pymysql
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    """Class to handle Cloud SQL database connections and queries."""
    
    def __init__(self):
        self.connector = Connector()
        self.instance_connection_name = os.getenv("INSTANCE_CONNECTION_NAME")
        self.db_user = os.getenv("DB_USER")
        self.db_pass = os.getenv("DB_PASS")
        self.db_name = os.getenv("DB_NAME")
        
        if not all([self.instance_connection_name, self.db_user, self.db_pass, self.db_name]):
            logger.error("Missing required environment variables")
            raise ValueError("Missing required environment variables")

    def execute_query(self, query, params=None, fetch=False):
        """Execute a query and return results if fetch is True."""
        try:
            with self.connector.connect(
                self.instance_connection_name,
                "pymysql",
                user=self.db_user,
                password=self.db_pass,
                db=self.db_name,
                ip_type=IPTypes.PUBLIC
            ) as conn:
                cursor = conn.cursor(dictionary=True)
                try:
                    cursor.execute(query, params or ())
                    if fetch:
                        result = cursor.fetchall()
                        conn.commit()
                        logger.debug(f"Query fetched: {result}")
                        return result or []
                    else:
                        conn.commit()
                        logger.debug(f"Query executed, rows affected: {cursor.rowcount}")
                        return cursor.rowcount
                except Exception as e:
                    logger.error(f"Query error: {e}")
                    raise
                finally:
                    cursor.close()
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise