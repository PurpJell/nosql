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
        
        result = session.run("MATCH (a:Airport {code: $code}) RETURN a", code=code)
        airport_data = result.single()
        if airport_data:
            return jsonify({"error": "Airport already exists."}), 400

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


@app.route('/airports/<code>', methods=['GET'])
def get_airport(code):
    # Define the Cypher query to find the airport by code
    query = """
    MATCH (a:Airport {code: $code})
    RETURN a
    """
    # Execute the query
    with driver.session() as session:
        result = session.run(query, code=code)
        airport_data = result.single()
        if airport_data:
            # Extract airport details from the result
            airport = {
                'code': airport_data['a']['code'],
                'name': airport_data['a']['name'],
                'numberOfTerminals': airport_data['a']['numberOfTerminals'],
                'address': airport_data['a']['address']
            }
            return jsonify(airport), 200
        else:
            return jsonify({"error": "Airport not found."}), 404


@app.route('/flights', methods=['PUT'])
def register_flight():
    # Get the JSON data from the request
    data = request.get_json()

    # Validate the payload
    try:
        flight_number = data['number']
        from_airport = data['fromAirport']
        to_airport = data['toAirport']
        price = data['price']
        flight_time = data['flightTimeInMinutes']
        operator = data['operator']
    except KeyError:
        return jsonify({"error": "Flight could not be created due to missing data."}), 400

    # Check if the source and destination airports exist
    with driver.session() as session:
        result_from = session.run("MATCH (a:Airport {code: $code}) RETURN a", code=from_airport)
        result_to = session.run("MATCH (a:Airport {code: $code}) RETURN a", code=to_airport)

        if not result_from.single() or not result_to.single():
            return jsonify({"error": "Flight could not be created because one or both airports do not exist."}), 400

        # Check if the flight already exists (by flight number)
        result_flight = session.run("MATCH (f:Flight {number: $number}) RETURN f", number=flight_number)
        if result_flight.single():
            return jsonify({"error": "Flight with the given number already exists."}), 400

    # Define the Cypher query to create the flight
    query = """
    MATCH (from:Airport {code: $fromAirport}), (to:Airport {code: $toAirport})
    CREATE (f:Flight {number: $number, price: $price, flightTimeInMinutes: $flightTime, operator: $operator})
    CREATE (f)-[:DEPARTS_FROM]->(from)
    CREATE (f)-[:ARRIVES_AT]->(to)
    RETURN f
    """
    # Execute the query
    with driver.session() as session:
        session.run(query, 
                    number=flight_number, 
                    fromAirport=from_airport, 
                    toAirport=to_airport, 
                    price=price, 
                    flightTime=flight_time, 
                    operator=operator)

    # Return success response
    return jsonify({"message": "Flight created."}), 201

@app.route('/flights/<number>', methods=['GET'])
def get_flight(number):
    """
    Get full flight information by flight number.
    Returns:
        200: Flight information in JSON format.
        404: If the flight is not found.
    """
    # Define the Cypher query
    query = """
    MATCH (f:Flight {number: $number})-[:DEPARTS_FROM]->(fromAirport:Airport)-[:LOCATED_IN]->(fromCity:City),
          (f)-[:ARRIVES_AT]->(toAirport:Airport)-[:LOCATED_IN]->(toCity:City)
    RETURN f, fromAirport, fromCity, toAirport, toCity
    """
    
    with driver.session() as session:
        # Execute the query
        result = session.run(query, number=number)
        flight_data = result.single()
        
        # Check if the flight exists
        if not flight_data:
            return jsonify({"error": "Flight not found."}), 404
        
        # Extract flight details
        flight_node = flight_data['f']
        from_airport_node = flight_data['fromAirport']
        from_city_node = flight_data['fromCity']
        to_airport_node = flight_data['toAirport']
        to_city_node = flight_data['toCity']
        
        # Create the response object
        flight = {
            "number": flight_node["number"],
            "fromAirport": from_airport_node["code"],
            "fromCity": from_city_node["name"],
            "toAirport": to_airport_node["code"],
            "toCity": to_city_node["name"],
            "price": flight_node["price"],
            "flightTimeInMinutes": flight_node["flightTimeInMinutes"],
            "operator": flight_node["operator"]
        }
        
        return jsonify(flight), 200

@app.route('/search/flights/<fromCity>/<toCity>', methods=['GET'])
def search_flights(fromCity, toCity):
    query = """
    MATCH (from:City {name: $fromCity})<-[:LOCATED_IN]-(fromAirport:Airport)<-[:DEPARTS_FROM]-(f:Flight)-[:ARRIVES_AT]->(toAirport:Airport)-[:LOCATED_IN]->(to:City {name: $toCity})
    RETURN 
        fromAirport.code AS fromAirport,
        toAirport.code AS toAirport,
        f.number AS flightNumber,
        f.price AS price,
        f.flightTimeInMinutes AS flightTime
    ORDER BY f.price
    LIMIT 1
    """
    
    with driver.session() as session:
        result = session.run(query, fromCity=fromCity, toCity=toCity)
        flight_data = result.single()
        
        if flight_data:
            response = {
                "fromAirport": flight_data["fromAirport"],
                "toAirport": flight_data["toAirport"],
                "flightNumber": flight_data["flightNumber"],
                "price": flight_data["price"],
                "flightTime": flight_data["flightTime"]
            }
            return jsonify(response), 200
        else:
            return jsonify({"error": "No flights found."}), 404


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
    return jsonify({"message": "Cleanup successful."}), 200

# Start the Flask app
if __name__ == '__main__':
    app.run(debug=True, port=5001)
