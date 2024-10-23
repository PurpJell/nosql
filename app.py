from flask import Flask, jsonify, request
from pymongo import MongoClient

app = Flask(__name__)

# Connect to local MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["lab"]
clientsColl = db["clients"]
productsColl = db["products"]
ordersColl = db["orders"]


@app.route('/clients/<clientId>', methods=['GET'])
def get_client(clientId):
    # Retrieve the client document by clientId
    client = clientsColl.find_one({"id": clientId}, {"_id": 0})  # Hide the MongoDB ObjectID in response
    
    if client:
        return jsonify({"message": "Client details", "client": client}), 200
    else:
        return jsonify({"error": "Client not found"}), 404

@app.route('/clients', methods=['PUT'])
def register_client():
    # Insert a new document
    new_data = request.json  # Expecting JSON input

    # Check if 'id', 'name', and 'email' are present in the request data
    if not new_data.get('id') or not new_data.get('name') or not new_data.get('email'):
        return jsonify({"error": "Invalid input, missing id, name or email"}), 400

    # Check if a document with the same id already exists
    existing_client = clientsColl.find_one({"id": new_data['id']})
    if existing_client:
        return jsonify({"error": "Client with this id already exists"}), 400  # Conflict error

    # Insert the new document into the collection
    clientsColl.insert_one(new_data)
    return jsonify({"message": "Client registered successfully", "clientId": new_data['id']}), 201

@app.route('/clients/<clientId>', methods=['DELETE'])
def delete_client(clientId):
    # Find and delete the client by clientId
    client = clientsColl.find_one({"id": clientId})

    if not client:
        return jsonify({"error": "Client not found"}), 404

    # Delete the client from the clients collection
    clientsColl.delete_one({"id": clientId})
    
    # Delete all orders associated with the client
    ordersColl.delete_many({"clientId": clientId})

    return jsonify({"message": "Client deleted "}), 200 # nes 204 neduoda contento !!!!!!!!!!!!!!!!!

@app.route('/products', methods=['PUT'])
def create_product():
    # Insert a new product
    new_product = request.json  # Expecting JSON input

    # Check if 'name' and 'price' are present in the request data
    if not new_product.get('name') or not new_product.get('price'):
        return jsonify({"error": "Invalid input, missing name or price"}), 400

    # Insert the new product into the products collection
    existing_product = productsColl.find_one({"id": new_product['id']})
    if existing_product:
        return jsonify({"error": "Product with this id already exists"}), 409  # Conflict error

   # Check if a product with the same name already exists
    existing_product_by_name = productsColl.find_one({"name": new_product['name']})
    if existing_product_by_name:
        return jsonify({"error": "Product with this name already exists"}), 409  # Conflict error

    productsColl.insert_one(new_product)
    
    return jsonify({"message": "Product registered successfully", "productId": new_product['id']}), 201

@app.route('/products', methods=['GET'])
def list_products():
    # Get the 'category' parameter from the query string (if provided)
    category = request.args.get('category')

    if category:
        # If a category is specified, filter products by category
        products = list(productsColl.find({"category": category}, {"_id": 0}))  # Exclude MongoDB ObjectID from the response
    else:
        # If no category is specified, return all products
        products = list(productsColl.find({}, {"_id": 0}))  # Exclude MongoDB ObjectID from the response

    return jsonify(products), 200

@app.route('/products/<productId>', methods=['GET'])
def get_product_details(productId):

    # Find the product by productId
    product = productsColl.find_one({"id": productId}, {"_id": 0})  # Exclude MongoDB ObjectID from the response

    if not product:
        return jsonify({"error": "Product not found"}), 404  # Return 404 if the product is not found

    return jsonify({"message": "Product details", "product": product}), 200  # Return the product details with a 200 status

@app.route('/products/<productId>', methods=['DELETE'])
def delete_product(productId):

    # Find the product by productId
    product = productsColl.find_one({"id": productId})

    if not product:
        return jsonify({"error": "Product not found"}), 404  # Return 404 if the product is not found

    # Delete the product from the products collection
    productsColl.delete_one({"id": productId})

    return jsonify({"message": "Product deleted"}), 200 #Vel 204 neduoda zinutes  # Return 204 status code on successful deletion

@app.route('/cleanup', methods=['POST'])
def cleanup_database():

    # Delete all documents from the clients collection
    clientsColl.delete_many({})
    # Delete all documents from the products collection
    productsColl.delete_many({})
    # Delete all documents from the orders collection
    ordersColl.delete_many({})

    db.counters.update_one(
        {'_id': 'orderid'},
        {'$set': {'sequence_value': 0}},
        upsert=True
    )

    return jsonify({"message": "Data deleted"}), 204  # Return 204 No Content on successful cleanup

@app.route('/orders', methods=['PUT'])
def create_order():

    # Insert a new order
    new_order = request.json

    # Check if 'clientId', 'productId', and 'quantity' are present in the request data
    if not new_order.get('clientId') or not new_order.get('items'):
        return jsonify({"error": "Invalid input, missing clientId, or items"}), 400
    
    # Check if the client exists
    client = clientsColl.find_one({"id": new_order['clientId']})
    if not client:
        return jsonify({"error": "Client not found"}), 404

    new_order['id'] = get_next_sequence_value('orderid')
    
    # Insert the new order into the orders collection
    ordersColl.insert_one(new_order)

    return jsonify({"message": "Order created", "orderId": new_order['id']}), 201


@app.route('/clients/<clientId>/orders', methods=['GET'])
def get_client_orders(clientId):

    # Find all orders for the client
    orders = list(ordersColl.find({"clientId": clientId}, {"_id": 0}))

    return jsonify({"message": "Client orders", "orders": orders}), 200

@app.route('/statistics/top/clients', methods=['GET'])
def get_top_clients():

    # Aggregate the total order amount for each client
    pipeline = [
        {"$group": {"_id": "$clientId", "totalOrders": {"$sum": 1}}},
        {"$sort": {"totalOrders": -1}},
        {"$limit": 10},
        {
            "$lookup": {
                "from": "clients",
                "localField": "_id",
                "foreignField": "id",
                "as": "client_info"
            }
        },
        {"$unwind": "$client_info"},
        {
            "$project": {
                "_id": 0,
                "clientId": "$_id",
                "totalOrders": 1,
                "clientName": "$client_info.name"
            }
        }
    ]

    top_clients = list(ordersColl.aggregate(pipeline))

    return jsonify({"message": "Top clients by number of orders placed", "topClients": top_clients}), 200


@app.route('/statistics/top/products', methods=['GET'])
def get_top_products():
    
        # Aggregate the total order amount for each product
        pipeline = [
            {"$unwind": "$items"},
            {"$group": {"_id": "$items.productId", "totalQuantity": {"$sum": "$items.quantity"}}},
            {"$sort": {"totalQuantity": -1}},
            {"$limit": 10},
            {
                "$lookup": {
                    "from": "products",
                    "localField": "_id",
                    "foreignField": "id",
                    "as": "product_info"
                }
            },
            {"$unwind": "$product_info"},
            {
                "$project": {
                    "_id": 0,
                    "productId": "$_id",
                    "totalQuantity": 1,
                    "productName": "$product_info.name"
                }
            }
        ]
    
        top_products = list(ordersColl.aggregate(pipeline))
    
        return jsonify({"message": "Top products by total quantity ordered", "topProducts": top_products}), 200

@app.route('/statistics/orders/total', methods=['GET'])
def get_total_orders():
    # Count the total number of orders
    total_orders = ordersColl.count_documents({})

    return jsonify({"message": "Orders statistics", "totalOrders": total_orders}), 200

@app.route('/statistics/orders/totalValue', methods=['GET'])
def get_total_order_value():
    # Calculate the total value of all orders
    pipeline = [
        {"$unwind": "$items"},
        {"$lookup": {
            "from": "products",
            "localField": "items.productId",
            "foreignField": "id",
            "as": "product_info"
        }},
        {"$unwind": "$product_info"},
        {"$group": {"_id": None, "totalValue": {"$sum": {"$multiply": ["$items.quantity", "$product_info.price"]}}}},
        {"$project": {"_id": 0, "totalValue": 1}}
    ]

    total_value = list(ordersColl.aggregate(pipeline))

    if total_value:
        return jsonify({"message": "Orders statistics", "totalValue": total_value[0]['totalValue']}), 200
    else:
        return jsonify({"message": "Orders statistics", "totalValue": 0}), 200


# autoincrementing sequence
def get_next_sequence_value(sequence_name):
    sequence_document = db.counters.find_one_and_update(
        {'_id': sequence_name},
        {'$inc': {'sequence_value': 1}},
        return_document=True,
        upsert=True
    )
    return sequence_document['sequence_value']



if __name__ == '__main__':
    app.run(debug=True)


    