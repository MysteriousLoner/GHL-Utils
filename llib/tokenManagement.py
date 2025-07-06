import logging
import requests
from datetime import datetime
from database.credentialsManagement import get_credentials, store_credentials
import os
from dotenv import load_dotenv

load_dotenv()

# Get environment variables
client_id = os.getenv('clientId')
client_secret = os.getenv('clientSecret')

# Configure logging
logger = logging.getLogger('tokenManagement')

def refresh_access_token(location_id):
    """
    Refresh the access token using the refresh token
    
    Args:
        location_id (str): The location ID to refresh tokens for
        
    Returns:
        bool: True if successful, False otherwise
        
    Raises:
        ValueError: If location_id is missing or credentials not found
        RuntimeError: If token refresh fails
    """
    if not location_id:
        error_msg = "Missing required parameter: location_id"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Get current credentials
    try:
        credentials = get_credentials(location_id)
        if not credentials or not credentials.refresh_token:
            error_msg = f"No refresh token found for location_id: {location_id}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    except Exception as e:
        error_msg = f"Failed to retrieve credentials: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    # Prepare refresh token request
    token_url = "https://services.leadconnectorhq.com/oauth/token"
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'refresh_token',
        'refresh_token': credentials.refresh_token,
        'user_type': 'Location'
    }
    
    try:
        logger.info(f"Refreshing access token for location_id: {location_id}")
        response = requests.post(token_url, headers=headers, data=data)
        response.raise_for_status()
        
        # Parse the response
        token_data = response.json()
        
        # Extract new tokens
        new_access_token = token_data.get('access_token')
        new_refresh_token = token_data.get('refresh_token')
        expires_in = token_data.get('expires_in')
        
        if not all([new_access_token, new_refresh_token, expires_in]):
            error_msg = "Incomplete token response from refresh request"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        # Store new credentials
        store_credentials(location_id, new_access_token, new_refresh_token, expires_in)
        
        logger.info(f"Successfully refreshed tokens for location_id: {location_id}")
        return True
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Failed to refresh token: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error during token refresh: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

def ensure_valid_token(location_id):
    """
    Check if the access token is expired and refresh if needed
    
    Args:
        location_id (str): The location ID to check
        
    Returns:
        str: Valid access token
        
    Raises:
        ValueError: If location_id is missing or credentials not found
        RuntimeError: If token refresh fails
    """
    if not location_id:
        error_msg = "Missing required parameter: location_id"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    try:
        credentials = get_credentials(location_id)
        if not credentials:
            error_msg = f"No credentials found for location_id: {location_id}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Check if token is expired
        if credentials.expires_at:
            expires_at = datetime.fromisoformat(credentials.expires_at)
            current_time = datetime.now()
            
            if current_time >= expires_at:
                logger.info(f"Token expired for location_id: {location_id}, refreshing...")
                refresh_access_token(location_id)
                # Get updated credentials
                credentials = get_credentials(location_id)
                if not credentials:
                    raise RuntimeError("Failed to retrieve updated credentials after refresh")
            else:
                logger.debug(f"Token still valid for location_id: {location_id}")
        
        return credentials.access_token
        
    except ValueError:
        # Re-raise ValueError
        raise
    except Exception as e:
        error_msg = f"Error ensuring valid token: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)