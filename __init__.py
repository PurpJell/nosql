import re
import werkzeug
import redis
from flask import (Flask, request, jsonify, abort)

licenseRegex = "^[A-Z0-9]{1,7}$"

userIdRegex = "^[A-Za-z0-9]{1,15}$"
userNameRegex = "^[A-Za-z\-]{1,15}$"

def create_app():
    app = Flask(__name__)
    redisClient = redis.Redis(host='localhost', port=6379, decode_responses=True)

    @app.route('/user/', methods=['PUT'])
    def put_user():
        reqBody = request.json
        userId = str(reqBody.get("id"))
        if redisClient.exists(userId) or re.search(userIdRegex, userId) == None:
            return { "message": "Toks vartotojas jau egzistuoja arba nenurodytas vartotojo ID." }, 400
        firstName = str(reqBody.get("firstName"))
        lastName = str(reqBody.get("lastName"))
        userName = firstName + ":" + lastName
        redisClient.set(userId, userName)
        return { "message": 'Vartotojo registracija sėkminga.'}, 200
        
    @app.route('/user/<userId>', methods=['GET'])
    def get_user(userId):
        if re.search(userIdRegex, userId) != None:
            userName = redisClient.get(userId)

            if (userName != None):
                name = userName.split(':')

                return {
                    "firstName": name[0],
                    "lastName": name[1]
                }
            else:
                return { "message": "User not found" }, 404
        else:
            return { "message": "Invalid userId" }, 400
        
    @app.route('/user/<userId>', methods=['DELETE'])
    def delete_user(userId):
        if redisClient.exists(userId) and re.search(userIdRegex, userId) != None:
            redisClient.delete(userId)

            return { "message": "Paskyra panaikinta sėkmingai." }, 200
        else:
            return { "message": "Paskyra nerasta." }, 404

    return app
    

