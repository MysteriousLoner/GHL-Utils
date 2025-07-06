from flask import Flask, request, jsonify, redirect
from types import SimpleNamespace
import os
from dotenv import load_dotenv
import logging
import requests
from database.credentialsManagement import store_credentials
from database.utils import init_db
from llib.queryInventory import get_inventory
from llib.checkInventory import check_inventory
from llib.sendMessage import send_email  # Add this import
from datetime import datetime

# Load environment variables
load_dotenv()
client_id = os.getenv('clientId')
client_secret = os.getenv('clientSecret')
domain = os.getenv('domain')
test_location_id = os.getenv('locationId')

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

# Check inventory endpoint
@app.route('/checkInventory', methods=['GET'])
def test_check_inventory():
    """Test endpoint to analyze inventory using location ID from environment"""
    try:
        if not test_location_id:
            return jsonify({
                "success": False,
                "message": "locationId not configured in environment variables"
            }), 500
        
        logger.info(f"Testing inventory check for location_id: {test_location_id}")
        
        # Get inventory using the queryInventory module
        inventory_data = get_inventory(test_location_id)
        
        # Analyze inventory using checkInventory module
        analysis_results = check_inventory(inventory_data)
        
        logger.info(f"Inventory analysis completed: {analysis_results['summary']}")
        
        return jsonify({
            "success": True,
            "message": f"Inventory analysis completed for location {test_location_id}",
            "data": {
                "location_id": test_location_id,
                "analysis": analysis_results,
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
            "message": f"Error analyzing inventory: {str(e)}"
        }), 500
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Unexpected error: {str(e)}"
        }), 500

# Test send email endpoint
@app.route('/testSendEmail', methods=['POST'])
def test_send_email():
    """Test endpoint to analyze inventory and send results via email"""
    try:
        # Get target email from request body
        request_data = request.get_json()
        if not request_data:
            return jsonify({
                "success": False,
                "message": "Request body is required"
            }), 400
        
        target_email = request_data.get('target_email')
        if not target_email:
            return jsonify({
                "success": False,
                "message": "target_email is required in request body"
            }), 400
        
        if not test_location_id:
            return jsonify({
                "success": False,
                "message": "locationId not configured in environment variables"
            }), 500
        
        logger.info(f"Processing inventory analysis and email for location_id: {test_location_id}")
        
        # Step 1: Get inventory data
        logger.info("Step 1: Fetching inventory data...")
        inventory_data = get_inventory(test_location_id)
        
        # Step 2: Analyze inventory
        logger.info("Step 2: Analyzing inventory...")
        analysis_results = check_inventory(inventory_data)
        
        # Step 3: Format results into a pretty table
        logger.info("Step 3: Formatting email content...")
        email_content = format_inventory_analysis_email(analysis_results, test_location_id)
        
        # Step 4: Send email
        logger.info(f"Step 4: Sending email to {target_email}...")
        send_email(
            target_email=target_email,
            message=email_content,
            subject=f"Inventory Analysis Report - Location {test_location_id}"
        )
        
        logger.info(f"Email sent successfully to {target_email}")
        
        return jsonify({
            "success": True,
            "message": f"Inventory analysis completed and email sent to {target_email}",
            "data": {
                "location_id": test_location_id,
                "target_email": target_email,
                "analysis_summary": analysis_results['summary'],
                "email_sent": True,
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
            "message": f"Error processing request: {str(e)}"
        }), 500
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Unexpected error: {str(e)}"
        }), 500

def format_inventory_analysis_email(analysis_results, location_id):
    """
    Format inventory analysis results into a pretty email message
    
    Args:
        analysis_results (dict): Results from check_inventory function
        location_id (str): The location ID being analyzed
        
    Returns:
        str: Formatted email content
    """
    # Extract data
    total_products = analysis_results.get('total_products', 0)
    in_stock_count = analysis_results.get('in_stock_count', 0)
    out_of_stock_count = analysis_results.get('out_of_stock_count', 0)
    out_of_stock_products = analysis_results.get('out_of_stock_products', [])
    
    email_content = f"""
INVENTORY ANALYSIS REPORT
========================

Location ID: {location_id}
Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SUMMARY
-------
Total Products:        {total_products}
In Stock Products:     {in_stock_count}
Out of Stock Products: {out_of_stock_count}

INVENTORY STATUS
---------------
"""
    
    if out_of_stock_count > 0:
        email_content += f"""
OUT OF STOCK ITEMS ({out_of_stock_count} items)
{'='*50}
{'Product Name':<30} {'Variant':<20} {'Qty':<5}
{'-'*55}
"""
        
        for product in out_of_stock_products[:20]:  # Limit to first 20 items
            product_name = product.get('product_name', 'Unknown')[:29]
            variant_name = product.get('variant_name', 'Unknown')[:19]
            quantity = product.get('available_quantity', 0)
            
            email_content += f"{product_name:<30} {variant_name:<20} {quantity:<5}\n"
        
        if len(out_of_stock_products) > 20:
            email_content += f"\n... and {len(out_of_stock_products) - 20} more items out of stock\n"
    else:
        email_content += "\n🎉 ALL PRODUCTS ARE IN STOCK! 🎉\n"
    
    email_content += f"""

RECOMMENDATIONS
--------------
"""
    
    if out_of_stock_count > 0:
        percentage_out = (out_of_stock_count / total_products) * 100 if total_products > 0 else 0
        email_content += f"• {percentage_out:.1f}% of products are out of stock\n"
        email_content += f"• Consider restocking the {out_of_stock_count} out-of-stock items\n"
        
        if percentage_out > 20:
            email_content += "• ⚠️ HIGH PRIORITY: Significant inventory shortage detected\n"
        elif percentage_out > 10:
            email_content += "• ⚡ MEDIUM PRIORITY: Notable inventory shortage\n"
        else:
            email_content += "• ✅ LOW PRIORITY: Minor inventory shortage\n"
    else:
        email_content += "• ✅ Inventory levels look great!\n"
        email_content += "• Continue monitoring stock levels regularly\n"
    
    email_content += f"""

---
This report was automatically generated by GHL Utils
For support, contact your system administrator
"""
    
    return email_content

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

if __name__ == '__main__':
    app.run(debug=True)