import re
import werkzeug
import redis
from flask import (Flask, request, jsonify, abort)

userIdRegex = "^[A-Za-z0-9]{1,15}$"
# userNameRegex = "^[A-Za-z\-]{1,15}$"

def create_app():
    app = Flask(__name__)
    redisClient = redis.Redis(host='localhost', port=6379, decode_responses=True)

    def viewKey(video_id):
        return f"video:{video_id}:views"
    
    def videoKey(video_id):
        return f"video:{video_id}" 
    
    def watchedVideoKey(user_id):
        return f"user:{user_id}:watched_videos"
    
    @app.route('/user/', methods=['PUT'])
    def put_user():
        reqBody = request.json
        userId = str(reqBody.get("id"))
        if redisClient.exists(userId) or re.search(userIdRegex, userId) == None:
            return { "message": "Toks vartotojas jau egzistuoja arba nenurodytas vartotojo ID." }, 400
        firstName = str(reqBody.get("firstName"))
        lastName = str(reqBody.get("lastName"))
        userName = firstName + ":" + lastName
        watchedVideos = []
        redisClient.set(userId, userName)
        for video in watchedVideos:
            redisClient.rpush(watchedVideoKey(userId), video)

        return { "message": 'Vartotojo registracija sėkminga.'}, 200
        
    @app.route('/user/<userId>', methods=['GET'])
    def get_user(userId):
        if re.search(userIdRegex, userId) != None:
            userName = redisClient.get(userId)
            
            #userName.pop('watchedVideos')

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

    @app.route('/video', methods=['PUT'])
    def register_video():
        reqBody = request.json
        video_id = reqBody.get("id")
        description = reqBody.get("description")
        length_in_s = reqBody.get("lengthInS")
        if redisClient.exists(videoKey(video_id)):
            return {"message": "Toks video jau egzistuoja"}, 400
        if video_id and description and isinstance(length_in_s, int):
            redisClient.hmset(videoKey(video_id), {
                "description": description,
                "lengthInS": length_in_s,
                "views": 0
            })
            return {"message": "Video uzregitruotas"}, 200
        else :
            return {"message": "Netinkami duomenys"}, 400
        
    @app.route('/video/<video_id>', methods=['GET'])
    def get_video(video_id):
        try:
            video_data = redisClient.hgetall(videoKey(video_id))

            if video_data:
                video_data.pop('views')
                # No need to decode; values are already strings
                return video_data, 200  # Return video information
            else:
                return {"message": "Video ID nerastas"}, 404  # Video ID not found
        except Exception as e:
            return {"message": str(e)}, 500  # Return the error message for debugging

    @app.route('/video/<video_id>/views', methods=['POST'])
    def register_view(video_id):
        reqBody = request.json
        user_id = reqBody.get("userId")
        if not redisClient.exists(videoKey(video_id)):
            return {"message": "Video ID nerastas"}, 404

        if re.search(userIdRegex, user_id) is not None:
            redisClient.incr(viewKey(video_id))
            if (not redisClient.exists(watchedVideoKey(user_id))):
                redisClient.rpush(watchedVideoKey(user_id), video_id)
            return {"message": "Peržiūra įregistruota."}, 200 
        else:
            return {"message": "Netinkamas naudotojo ID"}, 404
        
    @app.route('/video/<video_id>/views', methods=['GET'])
    def get_views(video_id):
        view_count = redisClient.get(viewKey(video_id))
        if view_count is not None:
            return {"views": int(view_count)}, 200 
        else:
            return {"message": "ID nerastas"}, 404
        
    @app.route('/user/<userId>/views', methods=['GET'])
    def get_watched_videos(userId):
        if not redisClient.exists(userId):
            return {"message": "Toks vartotojas neegzistuoja sistemoje"}, 404
        watched_videos = redisClient.lrange(watchedVideoKey(userId), 0, -1)
        if watched_videos:
            return {"watchedVideos": watched_videos}, 200
        
    return app