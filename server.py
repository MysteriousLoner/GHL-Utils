from flask import Flask, request, jsonify, redirect
from types import SimpleNamespace
import os
from dotenv import load_dotenv
import logging
import requests
from database.credentialsManagement import store_credentials
from database.utils import init_db
from llib.queryInventory import get_inventory, query_inventory_summary  # Add this import

# Load environment variables
load_dotenv()
client_id = os.getenv('clientId')
client_secret = os.getenv('clientSecret')
domain = os.getenv('domain')
test_location_id = os.getenv('locationId')  # Add this line

# configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('server')
# Initialize the database
init_db()

# Initialize Flask app
app = Flask(__name__)

# common apis start
# ping api to check if the server is running
@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({"message": "pong"})

# Test inventory endpoint
@app.route('/testInventory', methods=['GET'])
def test_inventory():
    """Test endpoint to get inventory using location ID from environment"""
    try:
        if not test_location_id:
            return jsonify({
                "success": False,
                "message": "locationId not configured in environment variables"
            }), 500
        
        logger.info(f"Testing inventory retrieval for location_id: {test_location_id}")
        
        # Get inventory using the queryInventory module
        inventory_data = get_inventory(test_location_id)
        
        # Extract inventory list
        inventory_list = inventory_data.get('inventory', [])
        total_count = inventory_data.get('total', [{}])[0].get('total', 0)
        
        logger.info(f"Successfully retrieved {len(inventory_list)} items from total of {total_count}")
        
        return jsonify({
            "success": True,
            "message": f"Retrieved inventory for location {test_location_id}",
            "data": {
                "location_id": test_location_id,
                "total_items": total_count,
                "items_retrieved": len(inventory_list),
                "inventory": inventory_list,
                "trace_id": inventory_data.get('traceId', '')
            }
        })
        
    except ValueError as e:
        logger.error(f"Invalid request: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Invalid request: {str(e)}"
        }), 400
        
    except RuntimeError as e:
        logger.error(f"Runtime error: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error retrieving inventory: {str(e)}"
        }), 500
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Unexpected error: {str(e)}"
        }), 500

# common apis end

# authentication api start
@app.route('/oauth/initiate', methods=['GET'])
def initiate_auth():
    # config variables for oauth initiation call
    configs = SimpleNamespace(
        baseUrl="https://marketplace.gohighlevel.com/oauth/chooselocation?",
        requestType="code",
        redirectUri=domain + "/oauth/callback",
        clientId=client_id,
        scopes=["products.readonly", "products/prices.readonly"],
    )

    # construct the redirect url for oauth initiation, can understand it as line being appended after line
    redirect_url = (
        f"{configs.baseUrl}"
        f"response_type={configs.requestType}&"
        f"redirect_uri={configs.redirectUri}&"
        f"client_id={configs.clientId}&"
        f"scope={' '.join(configs.scopes)}"
    )

    # used for debugging, returns the constructed redirect url
    # return jsonify({
    #     "message": "Redirecting to authentication",
    #     "redirect_url": redirect_url
    # })

    # redirect the caller to the constructed url
    return redirect(redirect_url)

@app.route('/oauth/callback', methods=['GET'])
def authenticate():
    """Handle OAuth callback and exchange code for tokens"""
    
    # Get the authorization code from the callback
    auth_code = request.args.get('code')
    state = request.args.get('state')
    
    # Add logging to see what we received
    logging.info(f"Received callback with code: {auth_code[:10] if auth_code else 'None'}...")
    logging.info(f"Received state: {state}")
    
    if not auth_code:
        return jsonify({
            "success": False,
            "message": "Authorization code not provided"
        }), 400
    
    # Prepare token exchange request
    token_url = "https://services.leadconnectorhq.com/oauth/token"
    
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'authorization_code',
        'code': auth_code,
        'user_type': 'Location'
    }
    
    # Add debugging for the request
    logging.info(f"Making token request to: {token_url}")
    logging.info(f"Request data: {dict(data)}")  # Don't log the actual secret
    
    try:
        # Make the token exchange request
        response = requests.post(token_url, headers=headers, data=data)
        
        # Log the response details before raising for status
        logging.info(f"Response status: {response.status_code}")
        logging.info(f"Response headers: {dict(response.headers)}")
        
        if response.status_code != 200:
            # Log the error response body
            try:
                error_body = response.json()
                logging.error(f"Error response body: {error_body}")
            except:
                logging.error(f"Error response text: {response.text}")
        
        response.raise_for_status()  # Raises an HTTPError for bad responses
        
        # Parse the response
        token_data = response.json()
        
        # Extract required data
        access_token = token_data.get('access_token')
        refresh_token = token_data.get('refresh_token')
        expires_in = token_data.get('expires_in')
        location_id = token_data.get('locationId')
        
        # Validate that we have all required data
        if not all([access_token, refresh_token, expires_in, location_id]):
            return jsonify({
                "success": False,
                "message": "Incomplete token response from OAuth provider"
            }), 500
        
        # Store credentials in database
        store_credentials(location_id, access_token, refresh_token, expires_in)
        
        return jsonify({
            "success": True,
            "message": "Authentication successful",
            "data": {
                "location_id": location_id,
                "company_id": token_data.get('companyId'),
                "user_type": token_data.get('userType'),
                "scope": token_data.get('scope'),
                "expires_in": expires_in
            }
        })
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Request exception: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Failed to exchange authorization code: {str(e)}"
        }), 500
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "message": f"Invalid request data: {str(e)}"
        }), 400
        
    except RuntimeError as e:
        return jsonify({
            "success": False,
            "message": f"Database error: {str(e)}"
        }), 500
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Unexpected error: {str(e)}"
        }), 500
# authentication api end