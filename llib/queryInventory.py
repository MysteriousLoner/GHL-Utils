import logging
import requests
import os
from dotenv import load_dotenv
from .tokenManagement import ensure_valid_token

load_dotenv()

# Get environment variables
client_id = os.getenv('clientId')
client_secret = os.getenv('clientSecret')

# Configure logging
logger = logging.getLogger('inventory')

def get_inventory(location_id):
    """
    Get all inventory items for a location
    
    Args:
        location_id (str): The location ID to get inventory for
        
    Returns:
        dict: Complete inventory response with all items
        
    Raises:
        ValueError: If location_id is missing
        RuntimeError: If API requests fail
    """
    if not location_id:
        error_msg = "Missing required parameter: location_id"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    try:
        # Ensure we have a valid access token
        access_token = ensure_valid_token(location_id)
        
        # API endpoint
        base_url = "https://services.leadconnectorhq.com/products/inventory"
        
        # Common headers
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {access_token}',
            'Version': '2021-07-28'
        }
        
        # Step 1: Get total count
        logger.info(f"Getting total inventory count for location_id: {location_id}")
        
        params_count = {
            'limit': 0,
            'altId': location_id,
            'altType': 'location'
        }
        
        response = requests.get(base_url, headers=headers, params=params_count)
        response.raise_for_status()
        
        count_data = response.json()
        
        # Extract total count
        total_items = 0
        if 'total' in count_data and len(count_data['total']) > 0:
            total_items = count_data['total'][0].get('total', 0)
        
        logger.info(f"Found {total_items} total items for location_id: {location_id}")
        
        if total_items == 0:
            return {
                'inventory': [],
                'total': [{'total': 0}],
                'traceId': count_data.get('traceId', '')
            }
        
        # Step 2: Get all items
        logger.info(f"Fetching all {total_items} inventory items for location_id: {location_id}")
        
        params_all = {
            'limit': total_items,
            'altId': location_id,
            'altType': 'location'
        }
        
        response = requests.get(base_url, headers=headers, params=params_all)
        response.raise_for_status()
        
        inventory_data = response.json()
        
        logger.info(f"Successfully retrieved {len(inventory_data.get('inventory', []))} items for location_id: {location_id}")
        
        return inventory_data
        
    except requests.exceptions.RequestException as e:
        error_msg = f"API request failed: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error getting inventory: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

def query_inventory_summary(location_id):
    """
    Get a summary of inventory for a location
    
    Args:
        location_id (str): The location ID to get summary for
        
    Returns:
        dict: Summary information about the inventory
    """
    try:
        inventory_data = get_inventory(location_id)
        
        items = inventory_data.get('inventory', [])
        total_count = inventory_data.get('total', [{}])[0].get('total', 0)
        
        # Calculate summary statistics
        total_available = sum(item.get('availableQuantity', 0) for item in items)
        unique_products = len(set(item.get('product', '') for item in items if item.get('product')))
        
        summary = {
            'location_id': location_id,
            'total_items': total_count,
            'total_available_quantity': total_available,
            'unique_products': unique_products,
            'items_with_stock': len([item for item in items if item.get('availableQuantity', 0) > 0]),
            'items_out_of_stock': len([item for item in items if item.get('availableQuantity', 0) == 0])
        }
        
        logger.info(f"Generated inventory summary for location_id: {location_id}")
        return summary
        
    except Exception as e:
        error_msg = f"Error generating inventory summary: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)