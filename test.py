from flask import Flask, request, jsonify
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement
from datetime import datetime

app = Flask(__name__)

# Connect to Cassandra
cluster = Cluster(['localhost'])  # Replace with your Cassandra cluster IP
session = cluster.connect('lab_keyspace')  # Replace with your keyspace name

@app.route('/setup', methods=['POST'])
def setup():

    create_tables_query = """
    CREATE TABLE IF NOT EXISTS channels (
        id TEXT PRIMARY KEY,
        owner TEXT,
        topic TEXT
    );
    """
    session.execute(create_tables_query)

    create_tables_query ="""
    CREATE TABLE IF NOT EXISTS channel_members (
        id TEXT,
        member TEXT,
        PRIMARY KEY (id, member)
    );
    """
    session.execute(create_tables_query)

    
    create_tables_query ="""
    CREATE TABLE IF NOT EXISTS messages (
        text TEXT,
        author TEXT,
        timestamp INT,
        PRIMARY KEY (text, author)
    );
    """
    session.execute(create_tables_query)

    create_tables_query = """
    CREATE TABLE IF NOT EXISTS channel_messages (
        channel_id TEXT,
        timestamp INT,
        author TEXT,
        text TEXT,
        PRIMARY KEY (channel_id, author, timestamp,  text)
    );
    """
    session.execute(create_tables_query)

    create_tables_query = """
    CREATE TABLE IF NOT EXISTS channel_messages_start_at (
        channel_id TEXT,
        timestamp INT,
        author TEXT,
        text TEXT,
        PRIMARY KEY (channel_id, timestamp, author, text)
    );
    """
    session.execute(create_tables_query)

    return jsonify({"message": "Setup completed."}), 201

@app.route('/channels', methods=['PUT'])
def register_channel():
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

@app.route('/channels/<channel_id>', methods=['GET'])
def get_channel(channel_id):
    # Retrieve the channel from Cassandra
    select_query = SimpleStatement("SELECT id, owner, topic FROM channels WHERE id = %s")
    result = session.execute(select_query, (channel_id,))
    
    channel = result.one()
    if not channel:
        return jsonify({"message": "Channel not found."}), 404

    return jsonify({
        "id": channel.id,
        "owner": channel.owner,
        "topic": channel.topic
    }), 200

@app.route('/channels/<channel_id>', methods=['DELETE'])
def delete_channel(channel_id):
    check_query = SimpleStatement("SELECT id FROM channels WHERE id = %s")
    result = session.execute(check_query, (channel_id,))
    
    if not result.one():
        return jsonify({"message": "Channel not found"}), 404
    
    delete_query = SimpleStatement("DELETE FROM channels WHERE id = %s")
    session.execute(delete_query, (channel_id,))
    
    return jsonify({"message": "Channel deleted."}), 204

@app.route('/channels/<channel_id>/messages', methods=['PUT'])
def add_message(channel_id):
    data = request.get_json()
    
    # Validate input
    if not data.get('text') or not data.get('author'):
        return jsonify({"message": "Invalid input, missing text or author."}), 400
    
    text = data['text']
    author = data['author']

    # Get the current maximum timestamp for the channel
    max_timestamp_query = SimpleStatement("""
        SELECT MAX(timestamp) AS max_timestamp FROM channel_messages WHERE channel_id = %s
    """)
    result = session.execute(max_timestamp_query, (channel_id,))
    max_timestamp_row = result.one()
    max_timestamp = max_timestamp_row.max_timestamp if max_timestamp_row.max_timestamp is not None else 0
    
    # Increment the message timestamp
    message_timestamp = max_timestamp + 1
    
    # Insert the new message into Cassandra
    insert_query = SimpleStatement("""
        INSERT INTO channel_messages (channel_id, author, timestamp, text)
        VALUES (%s, %s, %s, %s)
    """)
    session.execute(insert_query, (channel_id, author, message_timestamp, text))

    # Insert the new message into the channel_messages_start_at table
    insert_query = SimpleStatement("""
        INSERT INTO channel_messages_start_at (channel_id, timestamp, author, text)
        VALUES (%s, %s, %s, %s)
    """)
    session.execute(insert_query, (channel_id, message_timestamp, author, text))

    return jsonify({"message": "Message added."}), 201

@app.route('/channels/<channel_id>/messages', methods=['GET'])
def get_messages(channel_id):
    start_at = request.args.get('startAt')
    author = request.args.get('author')
    
    # Base query
    params = [channel_id]
    
    # Add filters based on parameters
    if author:
        query = "SELECT timestamp, author, text FROM channel_messages WHERE channel_id = %s"
        query += " AND author = %s"
        params.append(author)

        if start_at:
            query += " AND timestamp >= %s"
            params.append(int(start_at))

        messages_query = SimpleStatement(query + " ORDER BY author, timestamp ASC")

    else:
        query = "SELECT timestamp, author, text FROM channel_messages_start_at WHERE channel_id = %s"

        if start_at:
            query += " AND timestamp >= %s"
            params.append(int(start_at))
        messages_query = SimpleStatement(query + " ORDER BY timestamp ASC")

    rows = session.execute(messages_query, params)
    
    # Format results as a list of message dictionaries
    messages = [{"timestamp": row.timestamp, "author": row.author, "text": row.text} for row in rows]
    
    return jsonify(messages), 200

@app.route('/channels/<channel_id>/members', methods=['PUT'])
def add_member(channel_id):
    data = request.get_json()
    
    # Validate input
    if not data.get('member'):
        return jsonify({"message": "Invalid input, missing member."}), 400
    
    member = data['member']
    
    # Check if the channel exists
    check_channel_query = SimpleStatement("SELECT id FROM channels WHERE id = %s")
    channel_result = session.execute(check_channel_query, (channel_id,))
    
    if not channel_result.one():
        return jsonify({"message": "Channel not found."}), 400
    
    # Check if the member already exists in the channel
    check_member_query = SimpleStatement("SELECT member FROM channel_members WHERE id = %s AND member = %s")
    member_result = session.execute(check_member_query, (channel_id, member))
    
    if member_result.one():
        return jsonify({"message": "Member already exists in the channel."}), 400
    
    # Insert the new member into the channel_members table
    insert_query = SimpleStatement("""
        INSERT INTO channel_members (id, member)
        VALUES (%s, %s)
    """)
    session.execute(insert_query, (channel_id, member))
    
    return jsonify({"message": "Member added."}), 201

@app.route('/channels/<channel_id>/members', methods=['GET'])
def get_members(channel_id):

    # Check if the channel exists
    check_channel_query = SimpleStatement("SELECT id FROM channels WHERE id = %s")
    channel_result = session.execute(check_channel_query, (channel_id,))
    
    if not channel_result.one():
        return jsonify({"message": "Channel not found."}), 404

    # Retrieve the members from Cassandra
    select_query = SimpleStatement("SELECT member FROM channel_members WHERE id = %s")
    result = session.execute(select_query, (channel_id,))
    
    members = [row.member for row in result]
    return jsonify(members), 200

@app.route('/channels/<channel_id>/members/<member>', methods=['DELETE'])
def remove_member(channel_id, member):
    # Check if the member exists in the channel
    check_query = SimpleStatement("SELECT member FROM channel_members WHERE id = %s AND member = %s")
    result = session.execute(check_query, (channel_id, member))
    
    if not result.one():
        return jsonify({"message": "Member not found."}), 404
    
    # Delete the member from Cassandra
    delete_query = SimpleStatement("DELETE FROM channel_members WHERE id = %s AND member = %s")
    session.execute(delete_query, (channel_id, member))
    
    return jsonify({"message": "Member removed."}), 204


@app.route('/cleanup', methods=['POST'])
def cleanup():
    drop_tables_query = """
    DROP TABLE IF EXISTS channels;
    """
    session.execute(drop_tables_query)
    drop_tables_query = """
    DROP TABLE IF EXISTS channel_members;
    """
    session.execute(drop_tables_query)
    drop_tables_query = """
    DROP TABLE IF EXISTS messages;
    """
    session.execute(drop_tables_query)
    drop_tables_query = """
    DROP TABLE IF EXISTS channel_messages;
    """
    session.execute(drop_tables_query)

    drop_tables_query = """
    DROP TABLE IF EXISTS channel_messages_start_at;
    """
    session.execute(drop_tables_query)
    
    return jsonify({"message": "Cleanup completed."}), 200

@app.route('/channels/<channel_id>/len', methods=['GET'])
def get_channel_messages_count(channel_id):
    select_query = SimpleStatement("SELECT text FROM channel_messages WHERE channel_id = %s")
    result = session.execute(select_query, (channel_id,))
    
    messages = [row.text for row in result]
    return jsonify({"count": len(messages)}), 200


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)
