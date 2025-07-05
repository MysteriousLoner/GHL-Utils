import logging
from sqlite3 import Error
from datetime import datetime, timedelta
from . import utils

# Get the logger instance
logger = logging.getLogger('database')

def store_credentials(location_id, access_token, refresh_token, expires_in):
    """
    Store OAuth credentials in the database
    
    Args:
        location_id (str): The unique location identifier
        access_token (str): The OAuth access token
        refresh_token (str): The OAuth refresh token
        expires_in (int): Number of seconds until the access token expires
        
    Returns:
        bool: True if successful, False otherwise
        
    Raises:
        ValueError: If required parameters are missing
        RuntimeError: If database operations fail
    """
    # Input validation
    if not location_id:
        error_msg = "Missing required parameter: location_id"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    if not access_token:
        error_msg = "Missing required parameter: access_token" 
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    if not refresh_token:
        error_msg = "Missing required parameter: refresh_token"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    if not expires_in or not isinstance(expires_in, int):
        error_msg = "Invalid parameter: expires_in must be a valid integer"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Calculate expiration timestamp
    try:
        current_time = datetime.now()
        expires_at = current_time + timedelta(seconds=expires_in)  # Now using timedelta correctly
        
        logger.debug(f"Calculated token expiration: {expires_at} for location_id: {location_id}")
    except Exception as e:
        error_msg = f"Failed to calculate expiration timestamp: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    # Get database connection
    conn = utils.get_db_connection()
    if conn is None:
        error_msg = "Failed to establish database connection"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    try:
        cursor = conn.cursor()
        
        # Insert or replace the credentials
        cursor.execute('''
            INSERT OR REPLACE INTO users 
            (location_id, access_token, refresh_token, expires_at) 
            VALUES (?, ?, ?, ?)
        ''', (location_id, access_token, refresh_token, expires_at))
        
        # Commit the transaction
        conn.commit()
        
        logger.info(f"Successfully stored credentials for location_id: {location_id}")
        return True
    except Error as e:
        error_msg = f"Database error while storing credentials: {str(e)}"
        logger.error(error_msg)
        # Rollback in case of error
        if conn:
            conn.rollback()
        raise RuntimeError(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error while storing credentials: {str(e)}"
        logger.error(error_msg)
        # Rollback in case of error
        if conn:
            conn.rollback()
        raise RuntimeError(error_msg)
    finally:
        # Always close the connection
        if conn:
            conn.close()