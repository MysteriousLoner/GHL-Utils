from flask import Flask, request, jsonify, redirect
from types import SimpleNamespace
import os
from dotenv import load_dotenv
import logging
import requests
from database.credentialsManagement import store_credentials
from database.utils import init_db
from testEndpoints import test_bp  # Import the test blueprint

# Load environment variables
load_dotenv()
client_id = os.getenv('clientId')
client_secret = os.getenv('clientSecret')
domain = os.getenv('domain')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('server')

# Initialize the database
init_db()

# Initialize Flask app
app = Flask(__name__)

# Register test endpoints blueprint
app.register_blueprint(test_bp)

# Authentication API endpoints
@app.route('/oauth/initiate', methods=['GET'])
def initiate_auth():
    """Initiate OAuth authentication flow"""
    # Config variables for oauth initiation call
    configs = SimpleNamespace(
        baseUrl="https://marketplace.gohighlevel.com/oauth/chooselocation?",
        requestType="code",
        redirectUri=domain + "/oauth/callback",
        clientId=client_id,
        scopes=["products.readonly", "products/prices.readonly"],
    )

    # Construct the redirect url for oauth initiation
    redirect_url = (
        f"{configs.baseUrl}"
        f"response_type={configs.requestType}&"
        f"redirect_uri={configs.redirectUri}&"
        f"client_id={configs.clientId}&"
        f"scope={' '.join(configs.scopes)}"
    )

    # Redirect the caller to the constructed url
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
    logging.info(f"Request data: {dict(data)}")
    
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
        
        response.raise_for_status()
        
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)