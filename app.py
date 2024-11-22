from neo4j import GraphDatabase

# Define credentials and URI
uri = "bolt://localhost:7687"
username = "neo4j"
password = "password"

# Create a Neo4j driver instance
driver = GraphDatabase.driver(uri, auth=(username, password))

# Example function to test connection
def test_connection():
    with driver.session() as session:
        result = session.run("RETURN 'Hello, Neo4j!' AS message")
        for record in result:
            print(record["message"])

test_connection()
driver.close()
