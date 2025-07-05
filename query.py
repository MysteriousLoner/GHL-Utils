import json

with open('item.txt', 'r') as file:
    data = json.load(file)
    i = 0
    for product in data['inventory']:
        i = i + 1
    print(f"Total number of products: {i}")
    for product in data['inventory']:
        if product['availableQuantity'] == 0:
            print(f"Product Name: {product['productName']}, Available Quantity: {product['availableQuantity']}")
