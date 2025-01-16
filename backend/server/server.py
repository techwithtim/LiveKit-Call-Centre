# server.py
import os
from livekit import api
from flask import Flask, request
from dotenv import load_dotenv
from flask_cors import CORS
import uuid

load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})


async def generate_room_name():
    name = "room-" + str(uuid.uuid4())[:8]
    rooms = await get_rooms()
    while name in rooms:
        name = "room-" + str(uuid.uuid4())[:8]
    return name

@app.route('/getToken')
async def getToken():
    name = request.args.get('name', 'my name')  # Get name from query params, default to 'my name'
    room = request.args.get("room", None)
    
    if not room:
        room = await generate_room_name()

    token = api.AccessToken(os.getenv('LIVEKIT_API_KEY'), os.getenv('LIVEKIT_API_SECRET')) \
        .with_identity(name) \
        .with_name(name) \
        .with_grants(api.VideoGrants(
            room_join=True,
            room=room,
        ))

    return token.to_jwt()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)