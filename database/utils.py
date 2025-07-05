import sqlite3
import logging
from dotenv import load_dotenv
from sqlite3 import Error
import os
from datetime import datetime

load_dotenv()

logger = logging.getLogger('database')

# Define database directory and file path
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.getenv('dbDirName'))
DB_FILE = os.path.join(DATA_DIR, os.getenv('dbFileName'))

def ensure_data_dir_exists():
    """Ensure the data directory exists"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        logger.info(f"Created data directory at: {DATA_DIR}")

def get_db_connection():
    """Create a database connection to the SQLite database"""
    ensure_data_dir_exists()
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row  # This enables column access by name
        return conn
    except Error as e:
        logger.error(f"Database connection error: {e}")
        return None

def init_db():
    """Initialize the database with tables if they don't exist"""
    conn = get_db_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            
            # Check if users table already exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            table_exists = cursor.fetchone() is not None
            
            # Create users table for storing OAuth credentials
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    location_id TEXT PRIMARY KEY,
                    company_id TEXT,
                    access_token TEXT,
                    refresh_token TEXT,
                    expires_at TIMESTAMP
                )
            ''')
            
            conn.commit()
            
            # Log appropriate message based on whether table existed
            if table_exists:
                logger.info("Tables already exist, database ready to use")
            else:
                logger.info(f"Database initialized successfully with new tables at: {DB_FILE}")
            
            return True
        except Error as e:
            logger.error(f"Error initializing database: {e}")
            return False
        finally:
            conn.close()
    else:
        logger.error("Error: Could not establish database connection")
        return False

# Test the initialization function
if __name__ == "__main__":
    init_db()
