from flask import Flask, jsonify, request
from pymongo import MongoClient

app = Flask(__name__)

# Connect to local MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["lab"]
clientsColl = db["clients"]


@app.route('/clients/<clientId>', methods=['GET'])
def get_client(clientId):
    # Retrieve the client document by clientId
    client = clientsColl.find_one({"id": clientId}, {"_id": 0})  # Hide the MongoDB ObjectID in response
    
    if client:
        return jsonify({"message": "Client details", "client": client}), 200
    else:
        return jsonify({"error": "Client not found"}), 404

@app.route('/clients', methods=['PUT'])
def create_data():
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

    # Assuming you have an "orders" collection where client orders are stored
    ordersColl = db["orders"]
    
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
    productsColl = db["products"]  # Assuming there is a 'products' collection
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

    productsColl = db["products"]  # Assuming there is a 'products' collection

    if category:
        # If a category is specified, filter products by category
        products = list(productsColl.find({"category": category}, {"_id": 0}))  # Exclude MongoDB ObjectID from the response
    else:
        # If no category is specified, return all products
        products = list(productsColl.find({}, {"_id": 0}))  # Exclude MongoDB ObjectID from the response

    return jsonify(products), 200

@app.route('/products/<productId>', methods=['GET'])
def get_product_details(productId):
    productsColl = db["products"]  # Assuming there is a 'products' collection

    # Find the product by productId
    product = productsColl.find_one({"id": productId}, {"_id": 0})  # Exclude MongoDB ObjectID from the response

    if not product:
        return jsonify({"error": "Product not found"}), 404  # Return 404 if the product is not found

    return jsonify({"message": "Product details", "product": product}), 200  # Return the product details with a 200 status

@app.route('/products/<productId>', methods=['DELETE'])
def delete_product(productId):
    productsColl = db["products"]  # Assuming there is a 'products' collection

    # Find the product by productId
    product = productsColl.find_one({"id": productId})

    if not product:
        return jsonify({"error": "Product not found"}), 404  # Return 404 if the product is not found

    # Delete the product from the products collection
    productsColl.delete_one({"id": productId})

    return jsonify({"message": "Product deleted"}), 200 #Vel 204 neduoda zinutes  # Return 204 status code on successful deletion

@app.route('/cleanup', methods=['POST'])
def cleanup_database():
    # Assuming you have collections for clients and products
    clientsColl = db["clients"]
    productsColl = db["products"]
    ordersColl = db["orders"]

    # Delete all documents from the clients collection
    clientsColl.delete_many({})
    # Delete all documents from the products collection
    productsColl.delete_many({})
    # Delete all documents from the orders collection
    ordersColl.delete_many({})

    return jsonify({"message": "Data deleted"}), 204  # Return 204 No Content on successful cleanup


if __name__ == '__main__':
    app.run(debug=True)


    