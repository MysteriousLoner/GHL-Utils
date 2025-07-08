from flask import Blueprint, jsonify
import logging
import os
from dotenv import load_dotenv
from llib.queryInventory import get_inventory
from llib.checkInventory import check_inventory
from llib.sendMessage import send_email
from datetime import datetime

# Load environment variables
load_dotenv()
test_location_id = os.getenv('locationId')

# Configure logging
logger = logging.getLogger('test_endpoints')

# Create Blueprint for test endpoints
test_bp = Blueprint('test', __name__)

@test_bp.route('/ping', methods=['GET'])
def ping():
    """Health check endpoint"""
    return jsonify({"message": "pong"})

@test_bp.route('/testInventory', methods=['GET'])
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

@test_bp.route('/checkInventory', methods=['GET'])
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

@test_bp.route('/testSendEmail', methods=['GET'])
def test_send_email():
    """Test endpoint to analyze inventory and send results via email to predefined recipients"""
    try:
        # Hardcoded list of email addresses
        target_emails = [
            "kelvin@adrianwee.com",
            "kelinelam@adrianwee.com", 
            "johnny@adrianwee.com",
            "jinxuan@adrianwee.com",
            "leeyang4378@gmail.com"
        ]
        
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
        
        # Step 4: Send email to all recipients
        logger.info(f"Step 4: Sending emails to {len(target_emails)} recipients...")
        
        sent_emails = []
        failed_emails = []
        
        for email in target_emails:
            try:
                send_email(
                    target_email=email,
                    message=email_content,
                    subject=f"Inventory Analysis Report - Location {test_location_id}"
                )
                sent_emails.append(email)
                logger.info(f"Email sent successfully to {email}")
            except Exception as e:
                failed_emails.append({"email": email, "error": str(e)})
                logger.error(f"Failed to send email to {email}: {str(e)}")
        
        # Determine overall success
        overall_success = len(sent_emails) > 0
        
        return jsonify({
            "success": overall_success,
            "message": f"Inventory analysis completed. Emails sent to {len(sent_emails)} out of {len(target_emails)} recipients",
            "data": {
                "location_id": test_location_id,
                "total_recipients": len(target_emails),
                "emails_sent": len(sent_emails),
                "emails_failed": len(failed_emails),
                "sent_to": sent_emails,
                "failed_recipients": failed_emails,
                "analysis_summary": analysis_results['summary'],
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