import json
import logging

# Configure logging
logger = logging.getLogger('checkInventory')

def check_inventory(inventory_data):
    """
    Analyze inventory data and return statistics about products
    
    Args:
        inventory_data (dict): Response from queryInventory containing inventory data
        
    Returns:
        dict: Analysis results including total products and out-of-stock items
        
    Raises:
        ValueError: If inventory_data is invalid
    """
    if not inventory_data or not isinstance(inventory_data, dict):
        error_msg = "Invalid inventory data provided"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    try:
        # Extract inventory list from the data
        inventory_list = inventory_data.get('inventory', [])
        
        if not inventory_list:
            logger.warning("No inventory items found in the data")
            return {
                "total_products": 0,
                "out_of_stock_products": [],
                "out_of_stock_count": 0,
                "in_stock_count": 0,
                "summary": "No inventory items found"
            }
        
        # Count total products
        total_products = len(inventory_list)
        
        # Find out-of-stock products
        out_of_stock_products = []
        in_stock_count = 0
        
        for product in inventory_list:
            available_quantity = product.get('availableQuantity', 0)
            
            if available_quantity == 0:
                out_of_stock_products.append({
                    "product_name": product.get('productName', 'Unknown'),
                    "variant_name": product.get('name', 'Unknown'),
                    "available_quantity": available_quantity,
                    "product_id": product.get('product', ''),
                    "variant_id": product.get('_id', '')
                })
            else:
                in_stock_count += 1
        
        out_of_stock_count = len(out_of_stock_products)
        
        # Create summary
        summary = f"Total: {total_products} products, In Stock: {in_stock_count}, Out of Stock: {out_of_stock_count}"
        
        logger.info(f"Inventory analysis complete: {summary}")
        
        return {
            "total_products": total_products,
            "out_of_stock_products": out_of_stock_products,
            "out_of_stock_count": out_of_stock_count,
            "in_stock_count": in_stock_count,
            "summary": summary
        }
        
    except Exception as e:
        error_msg = f"Error analyzing inventory data: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

with open('item.txt', 'r') as file:
    data = json.load(file)
    check_inventory(data)
