from flask import Flask, jsonify, request
from pymongo import MongoClient

app = Flask(__name__)

# Connect to local MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["lab"]
clientsColl = db["clients"]

@app.route('/clients', methods=['GET'])
def get_data():
    # Retrieve all documents from the collection
    data = list(clientsColl.find({}, {"_id": 0}))  # Hide the MongoDB ObjectID in response
    return jsonify(data)

@app.route('/clients', methods=['POST'])
def create_data():
    # Insert a new document
    new_data = request.json  # Expecting JSON input
    clientsColl.insert_one(new_data)
    return jsonify({"message": "Data inserted successfully"}), 201

if __name__ == '__main__':
    app.run(debug=True)