from flask import Flask, request, jsonify
from neo4j import GraphDatabase

# Initialize the Flask app
app = Flask(__name__)

# Setup Neo4j driver (make sure to adjust your connection details)
uri = "bolt://localhost:7687"  # Change the URI if necessary
username = "neo4j"  # Neo4j default username
password = "password"  # Replace with your Neo4j password
driver = GraphDatabase.driver(uri, auth=(username, password))

# Custom endpoint to execute a Cypher query
@app.route('/cities', methods=['PUT'])
def register_city():
    # Get the JSON data from the request
    data = request.get_json()

    # Check if the JSON data is valid
    try:
        name = data['name']
        country = data['country']
    except KeyError:
        return jsonify({"error": "Could not register the city, it exists or mandatory attributes are missing."}), 400
    
    # Check if the city already exists
    with driver.session() as session:
        result = session.run("MATCH (c:City {name: $name}) RETURN c", name=name)
        city_data = result.single()
        if city_data:
            return jsonify({"error": "Could not register the city, it exists or mandatory attributes are missing."}), 400

    # Define the Cypher query
    query = "CREATE (c:City {name: $name, country: $country}) RETURN c"
    # Execute the query
    with driver.session() as session:
        result = session.run(query, name=name, country=country)

    # Return a success message
    return jsonify({"message": "City registered successfully."}), 201


@app.route('/cities', methods=['GET'])
def get_cities():
    # Define the Cypher query
    query = "MATCH (c:City) RETURN c"
    # Execute the query
    with driver.session() as session:
        result = session.run(query)
        # Extract the data from the result
        cities = [{'name': record['c']['name'], 'country': record['c']['country']} for record in result]
    # Return the cities data as JSON
    return jsonify(cities), 200


@app.route('/cities/<name>', methods=['GET'])
def get_city(name):
    # Define the Cypher query
    query = "MATCH (c:City {name: $name}) RETURN c"
    # Execute the query
    with driver.session() as session:
        result = session.run(query, name=name)
        # Extract the data from the result
        city_data = result.single()
        if city_data:
            city = {'name': city_data['c']['name'], 'country': city_data['c']['country']}
            return jsonify(city), 200
        else:
            return jsonify({"error": "City not found."}), 404
        

@app.route('/cities/<city>/airports', methods=['PUT'])
def register_airport(city):
    # Get the JSON data from the request
    data = request.get_json()

    # Check if the JSON data is valid
    try:
        code = data['code']
        name = data['name']
        number_of_terminals = data['numberOfTerminals']
        address = data['address']
        city = city
    except KeyError:
        return jsonify({"error": "Airport could not be created due to missing data or city the airport is registered in is not registered in the system."}), 400
    
    # Check if the city exists
    with driver.session() as session:
        result = session.run("MATCH (c:City {name: $city_name}) RETURN c", city_name=city)
        city_data = result.single()
        if not city_data:
            return jsonify({"error": "Airport could not be created due to missing data or city the airport is registered in is not registered in the system."}), 400
        
        result = session.run("MATCH (a:Airport {name: $name}) RETURN a", name=name)
        airport_data = result.single()
        if airport_data:
            return jsonify({"error": "Airport already exists."}), 400
        
    # Define the Cypher query
    query = """
    MATCH (c:City {name: $city_name})
    CREATE (a:Airport {code: $code, name: $name, numberOfTerminals: $numberOfTerminals, address: $address})-[:LOCATED_IN]->(c)
    RETURN a
    """
    # Execute the query
    with driver.session() as session:
        result = session.run(query,  city_name=city, code=code, name=name, numberOfTerminals=number_of_terminals, address=address)

    # Return a success message
    return jsonify({"message": "Airport created."}), 201


@app.route('/cities/<city>/airports', methods=['GET'])
def get_airports(city):

    # Check if the city exists
    with driver.session() as session:
        result = session.run("MATCH (c:City {name: $city_name}) RETURN c", city_name=city)
        city_data = result.single()
        if not city_data:
            return jsonify({"error": "City not found."}), 404

    # Define the Cypher query
    query = """
    MATCH (c:City {name: $city_name})<-[:LOCATED_IN]-(a:Airport)
    RETURN a
    """
    # Execute the query
    with driver.session() as session:
        result = session.run(query, city_name=city)
        # Extract the data from the result
        airports = [{'code': record['a']['code'], 'name': record['a']['name'], 'numberOfTerminals': record['a']['numberOfTerminals'], 'address': record['a']['address']} for record in result]
    # Return the airports data as JSON
    return jsonify(airports), 200


@app.route('/cities/<city>/airports/<code>', methods=['GET'])
def get_airport(city, code):
    # Check if the city exists
    with driver.session() as session:
        result = session.run("MATCH (c:City {name: $city_name}) RETURN c", city_name=city)
        city_data = result.single()
        if not city_data:
            return jsonify({"error": "City not found."}), 404

    # Define the Cypher query
    query = """
    MATCH (c:City {name: $city_name})<-[:LOCATED_IN]-(a:Airport {code: $code})
    RETURN a
    """
    # Execute the query
    with driver.session() as session:
        result = session.run(query, city_name=city, code=code)
        # Extract the data from the result
        airport_data = result.single()
        if airport_data:
            airport = {'code': airport_data['a']['code'], 'name': airport_data['a']['name'], 'numberOfTerminals': airport_data['a']['numberOfTerminals'], 'address': airport_data['a']['address']}
            return jsonify(airport), 200
        else:
            return jsonify({"error": "Airport not found."}), 404


@app.route('/cleanup', methods=['POST'])
def cleanup():
    # Define the Cypher query
    query = """
    MATCH (n)
    DETACH DELETE n
    """
    # Execute the query
    with driver.session() as session:
        session.run(query)
    # Return a success message
    return jsonify({"message": "Data deleted."}), 200

# Start the Flask app
if __name__ == '__main__':
    app.run(debug=True, port=5001)
