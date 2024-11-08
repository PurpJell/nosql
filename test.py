from flask import Flask, request, jsonify
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement

app = Flask(__name__)

# Connect to Cassandra
cluster = Cluster(['localhost'])  # Replace with your Cassandra cluster IP
session = cluster.connect('lab_keyspace')  # Replace with your keyspace name

# Define the CREATE TABLE query for channels
create_channels_table_query = """
CREATE TABLE IF NOT EXISTS channels (
    id TEXT PRIMARY KEY,
    owner TEXT,
    topic TEXT
);
"""

# Execute the query
session.execute(create_channels_table_query)
# Define the CREATE TABLE query
create_table_query = """
CREATE TABLE IF NOT EXISTS channel_members (
    id TEXT,
    member TEXT,
    PRIMARY KEY (id, member)
);
"""

# Execute the query
session.execute(create_table_query)

@app.route('/channels', methods=['PUT'])
def create_channel():
    data = request.get_json()
    
    # Validate input
    if not data.get('id') or not data.get('owner'):
        return jsonify({"message": "Invalid input, missing name or owner. Or the channel with such id already exists."}), 400
    
    channel_id = data['id']
    owner = data['owner']
    topic = data.get('topic', None)  # Default to None if topic is not provided

    # Check if the channel already exists
    check_query = SimpleStatement("SELECT id FROM channels WHERE id = %s")
    result = session.execute(check_query, (channel_id,))
    
    if result.one():
        return jsonify({"message": "Channel with such id already exists."}), 400

    # Insert the new channel into Cassandra
    insert_query = SimpleStatement("""
        INSERT INTO channels (id, owner, topic)
        VALUES (%s, %s, %s)
    """)
    session.execute(insert_query, (channel_id, owner, topic))
    
    # Optionally add the owner as a member to the channel
    insert_member_query = SimpleStatement("""
        INSERT INTO channel_members (id, member)
        VALUES (%s, %s)
    """)
    session.execute(insert_member_query, (channel_id, owner))
    
    return jsonify({"id": channel_id}), 201

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)
