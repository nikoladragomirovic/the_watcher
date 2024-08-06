from flask import Flask, request, jsonify, g
from pymongo import MongoClient
from minio import Minio
from datetime import datetime, timedelta
from flask_cors import CORS
import bcrypt
import secrets
import string
import requests
import os
import face_recognition
import numpy as np
from flask_socketio import SocketIO, emit
import cv2
from functools import wraps

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})
socketio = SocketIO(app, cors_allowed_origins="*")

# GLOBALS #

minio_client = Minio("127.0.0.1:9000",
                     access_key="minioadmin",
                     secret_key="minioadmin",
                     secure=False)

mongo_client = MongoClient('mongodb://localhost:27017/')
database = mongo_client['the_watcher']

telegram_bot_token = os.environ.get('THE_WATCHER_TOKEN')

# END GLOBALS #

# HELPER FUNCTIONS #

def generate_session_token():
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(32))

def check_session_token(username, session_token):
    user = database['accounts'].find_one({'username': username, 'session_tokens': session_token})
    return user is not None

def get_cameras(username):
    user = database['accounts'].find_one({'username': username})
    return user.get('cameras', 'Field not found') if user else 'Field not found'

def send_telegram_notification(chat_id, text, image_bytes):
    url = f"https://api.telegram.org/bot{telegram_bot_token}/sendPhoto"

    files = {
        'photo': ('image.jpg', image_bytes, 'image/jpeg')
    }
    data = {
        'chat_id': chat_id,
        'caption': text
    }

    response = requests.post(url, files=files, data=data)
    return response.json()

# END HELPER FUNCTIONS #

# DECORATORS #

def auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        username = request.form.get('username')
        session_token = request.form.get('session_token')

        if not username or not session_token:
            return jsonify({'error': 'Username or session token missing'}), 400

        if not check_session_token(username, session_token):
            return jsonify({'error': 'Invalid session token'}), 401

        g.username = username
        return f(*args, **kwargs)
    return decorated_function

# END DECORATORS #

# UPLOAD FUNCTION #
    
@app.route('/upload', methods=['POST'])
def upload_image():
    camera_id = request.form.get('camera_id')
    file = request.files['image']

    encodings = []
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    filename = f"{timestamp}.jpg"

    camera = database['accounts'].find_one({'cameras': {'$elemMatch': {'id': camera_id}}})
    chat_id = camera['chat_id']
    username = camera['username']

    if 'image' not in request.files:
        return jsonify({'error': 'No image part'}), 400
    
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if camera: 
        faces = camera.get('faces', [])
        encodings = [face['encoding'] for face in faces]

    try:
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)

        image_bytes = file.read()
        image_np = np.frombuffer(image_bytes, np.uint8)
        image_np = cv2.imdecode(image_np, cv2.IMREAD_COLOR)

        file.seek(0)

        unknown = face_recognition.face_encodings(image_np)
        results = face_recognition.compare_faces(np.array(encodings), unknown)

        if not minio_client.bucket_exists(camera_id):
            minio_client.make_bucket(camera_id)

        if True in results:
            recognized_face = camera['faces'][results.index(True)]['name']
            send_telegram_notification(chat_id, f"{recognized_face} is at your door!", image_bytes)
            return jsonify({'message': 'Face recognized, no need for upload'}), 200

        minio_client.put_object(camera_id, filename, file, file_size)
        send_telegram_notification(chat_id, "Someone at your door, visit http://127.0.0.1:3000 to check it out!", image_bytes)
        socketio.emit('new_frame', {'username': username})

        return jsonify({'message': 'Image uploaded successfully', 'filename': filename}), 200
    except Exception as e:
        return str(e)
    
# END UPLOAD FUNCTION #

# CAMERA MANAGMENT ROUTES #

@app.route('/enroll', methods=['POST'])
@auth_required
def enroll_camera():
    camera_id = request.form.get('camera_id')
    camera_name = request.form.get('name')

    user = database['accounts'].find_one({'username': g.username})
    existing_camera = database['accounts'].find_one({'cameras.id': camera_id})

    if any(camera['id'] == camera_id for camera in user['cameras']):
        return jsonify({'message': 'Camera already registered to your account'}), 409
    
    if existing_camera:
        return jsonify({'message': 'Camera already registered to an account'}), 303
    
    if minio_client.bucket_exists(camera_id) is False:
        return jsonify({'message': 'Camera with this id does not exist'}), 401

    result = database['accounts'].update_one(
        {'username': g.username},
        {'$push': {'cameras': {'name': camera_name, 'id': camera_id}}}
    )
    
    if result.modified_count > 0:
        return jsonify({'message': 'Camera added successfully'}), 200
    else:
        return jsonify({'message': 'Failed to add camera'}), 500


@app.route('/exclude', methods=['POST'])
@auth_required
def exclude_camera():
    camera_id = request.form.get('camera_id')

    result = database['accounts'].update_one(
        {'username': g.username},
        {'$pull': {'cameras': {'id': camera_id}}}
    )

    if result.modified_count > 0:
        return jsonify({'message': 'Camera removed from account'}), 200
    else:
        return jsonify({'message': 'Failed to remove camera or camera not found'}), 404

@app.route('/rename', methods=['POST'])
@auth_required
def rename_camera():
    camera_id = request.form.get('camera_id')
    name = request.form.get('name')
    
    result = database['accounts'].update_one(
        {'username': g.username, 'cameras.id': camera_id},
        {'$set': {'cameras.$[elem].name': name}},
        array_filters=[{'elem.id': camera_id}]
    )

    if result.modified_count > 0:
        return jsonify({'message': 'Successfully renamed camera'}), 200
    else:
        return jsonify({'message': 'Camera not found or name unchanged'}), 404
    
# END CAMERA MANAGMENT ROUTES #

# FRAME MANAGMENT ROUTES #
    
@app.route('/clear', methods=['POST'])
@auth_required
def clear_picture():
    camera_id = request.form.get('camera_id')
    image_name = request.form.get('image_name')

    minio_client.remove_object(camera_id, image_name)

    return jsonify({'message': 'Successfully deleted image'})

@app.route('/frames', methods=['POST'])
@auth_required
def get_frames():
    cameras = get_cameras(g.username)
    data = []

    for camera in cameras:
        id = camera['id']
        objects = minio_client.list_objects(str(id), recursive=True)

        for obj in objects:
            url = minio_client.presigned_get_object(str(id), obj.object_name, expires=timedelta(hours=1),)
            data.append({"url": url, "date": obj.object_name.split('.')[0].split(' ')[0],"time": obj.object_name.split('.')[0].split(' ')[1], "cameraName": camera['name'], 'cameraId': id, 'name': obj.object_name})
    
    return jsonify(data)

# END FRAME MANAMENT ROUTES #

# FACE MANAGMENT ROUTES #

@app.route('/save', methods=['POST'])
@auth_required
def save_face():
    name = request.form.get('name')
    camera_id = request.form.get('camera_id')
    frame_name = request.form.get('frame_name')

    try:
        response = minio_client.get_object(camera_id, frame_name)
        
        image_bytes = response.read()
        response.close()
        response.release_conn()
        
        image_np = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
        
        face_encodings = face_recognition.face_encodings(image)
        
        if len(face_encodings) == 0:
            return jsonify({'error': 'No faces found in the image'}), 400

        face_encoding = face_encodings[0]
        face_encoding_list = face_encoding.tolist()

        if database['accounts'].find_one({'username': g.username, 'faces.name': name}) is not None:
            return jsonify({"message": "Name already exists"}), 409

        user = database['accounts'].find_one({'username': g.username})
        existing_encodings = [face['encoding'] for face in user.get('faces', [])]

        matches = face_recognition.compare_faces(np.array(existing_encodings), face_encoding)

        if True in matches:
            return jsonify({"message": "Face encoding already exists"}), 303

        saved_face = {"name": name, "encoding": face_encoding_list}

        result = database['accounts'].update_one(
            {'username': g.username},
            {'$push': {'faces': saved_face}}
        )

        return jsonify({"message": "Face saved successfully"}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/delete', methods=['POST'])
@auth_required
def delete_face():
    name = request.form.get('name')
    
    try:
        result = database['accounts'].update_one(
        {'username': g.username},
        {'$pull': {'faces': {'name': name}}})

        return jsonify('Face deleted'), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# END FACE MANAGMENT ROUTES #

# SETTINGS ROUTES #
    
@app.route('/settings', methods=['POST'])
@auth_required
def get_faces():
    try:
        user = database['accounts'].find_one({'username': g.username})

        if user is None:
            return jsonify({'error': 'User not found'}), 404

        faces = user.get('faces', [])
        face_names = [face.get('name') for face in faces if 'name' in face]

        chat_id = user.get('chat_id')

        return jsonify({'faces': face_names, 'cameras': get_cameras(g.username), 'chat_id': chat_id}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/telegram', methods=['POST'])
@auth_required
def telegram():
    chat_id = request.form.get('chat_id')

    if not chat_id:
        return jsonify({'error': 'Chat ID missing'}), 400

    try:
        result = database['accounts'].update_one(
            {'username': g.username},
            {'$set': {'chat_id': chat_id}}
        )

        if result.modified_count > 0:
            return jsonify({'message': 'Chat ID updated successfully'}), 200
        else:
            return jsonify({'message': 'Failed to update Chat ID'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
# END SETTINGS ROUTES #

# USER ROUTES #
    
@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        return jsonify({'error': 'Username or password missing'}), 400

    existing_user = database['accounts'].find_one({'username': username})
    if existing_user:
        return jsonify({'error': 'Username already exists'}), 409

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    session_token = generate_session_token()

    new_user = {
        'username': username,
        'password': hashed_password.decode('utf-8'),
        'session_tokens': [session_token],
        'chat_id': "",
        'cameras': [],
        'faces': []
    }
    database['accounts'].insert_one(new_user)

    return jsonify({'message': 'User registered successfully', 'session_token': session_token}), 201

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        return jsonify({'error': 'Username or password missing'}), 400

    existing_user = database['accounts'].find_one({'username': username})
    if not existing_user:
        return jsonify({'error': 'Username does not exist'}), 404

    hashed_password = existing_user['password'].encode('utf-8')

    if bcrypt.checkpw(password.encode('utf-8'), hashed_password):
        session_token = generate_session_token()
        database['accounts'].update_one({'username': username}, {'$push': {'session_tokens': session_token}})

        return jsonify({'message': 'Login successful', 'session_token': session_token}), 200
    else:
        return jsonify({'error': 'Incorrect password'}), 401

@app.route('/logout', methods=['POST'])
@auth_required
def logout():
    database['accounts'].update_one({'username': g.username}, {'$pull': {'session_tokens': request.form.get('session_token')}})
    return jsonify({'message': 'Logout successful'}), 200

# END USER ROUTES #

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
