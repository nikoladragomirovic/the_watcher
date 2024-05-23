from flask import Flask, request, jsonify, abort
from pymongo import MongoClient
from minio import Minio
from datetime import datetime
from flask_cors import CORS
import bcrypt
import secrets
import string
import os

app = Flask(__name__)
CORS(app, origins='*')

database_name = 'the_watcher'
minio_client = Minio("127.0.0.1:9000",
                     access_key="minioadmin",
                     secret_key="minioadmin",
                     secure=False)

def generate_session_token():
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(32))

def check_session_token(username, session_token):
    client = MongoClient('mongodb://localhost:27017/')
    db = client[database_name]
    accounts_collection = db['accounts']

    user = accounts_collection.find_one({'username': username, 'session_tokens': session_token})
    client.close()
    return user is not None

def get_cameras(username):
    client = MongoClient('mongodb://localhost:27017/')
    db = client[database_name]
    accounts_collection = db['accounts']

    user = accounts_collection.find_one({'username': username})
    if user is not None:
        cameras = user.get('cameras', 'Field not found')

    client.close()
    return cameras

@app.route('/upload', methods=['POST'])
def upload_image():
    camera_id = request.form.get('camera_id')

    if 'image' not in request.files:
        return jsonify({'error': 'No image part'}), 400
    
    file = request.files['image']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    filename = f"{timestamp}.jpg"
    
    try:
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)

        if not minio_client.bucket_exists(camera_id):
            minio_client.make_bucket(camera_id)

        minio_client.put_object(camera_id, filename, file, file_size)
        return jsonify({'message': 'Image uploaded successfully', 'filename': filename}), 200
    except Exception as e:
        return str(e)

@app.route('/frames', methods=['POST'])
def get_frames():
    username = request.form.get('username')
    session_token = request.form.get('session_token')

    if not username or not session_token:
        return jsonify({'error': 'Username or session token missing'}), 400

    if not check_session_token(username, session_token):
        return jsonify({'error': 'Invalid session token'}), 401
    
    cameras = get_cameras(username)
    images = []

    for camera in cameras:
        objects = minio_client.list_objects(str(camera), recursive=True)

        for obj in objects:
            url = minio_client.presigned_get_object(str(camera), obj.object_name)
            images.append({"url": url, "camera": camera, "time": obj.object_name.split('.')[0]})
    
    return jsonify(images)
    
@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        return jsonify({'error': 'Username or password missing'}), 400

    client = MongoClient('mongodb://localhost:27017/')
    db = client[database_name]
    accounts_collection = db['accounts']

    existing_user = accounts_collection.find_one({'username': username})
    if existing_user:
        return jsonify({'error': 'Username already exists'}), 409

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    session_token = generate_session_token()

    new_user = {
        'username': username,
        'password': hashed_password.decode('utf-8'),
        'session_tokens': [session_token],
        'cameras': []
    }
    accounts_collection.insert_one(new_user)
    client.close()

    return jsonify({'message': 'User registered successfully', 'session_token': session_token}), 201

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        return jsonify({'error': 'Username or password missing'}), 400

    client = MongoClient('mongodb://localhost:27017/')
    db = client[database_name]
    accounts_collection = db['accounts']

    existing_user = accounts_collection.find_one({'username': username})
    if not existing_user:
        return jsonify({'error': 'Username does not exist'}), 404

    hashed_password = existing_user['password'].encode('utf-8')

    if bcrypt.checkpw(password.encode('utf-8'), hashed_password):
        session_token = generate_session_token()
        accounts_collection.update_one({'username': username}, {'$push': {'session_tokens': session_token}})

        client.close()

        return jsonify({'message': 'Login successful', 'session_token': session_token}), 200
    else:
        client.close()

        return jsonify({'error': 'Incorrect password'}), 401

@app.route('/logout', methods=['POST'])
def logout():
    username = request.form.get('username')
    session_token = request.form.get('session_token')

    if not username or not session_token:
        return jsonify({'error': 'Username or session token missing'}), 400

    client = MongoClient('mongodb://localhost:27017/')
    db = client[database_name]
    accounts_collection = db['accounts']

    accounts_collection.update_one({'username': username}, {'$pull': {'session_tokens': session_token}})

    client.close()

    return jsonify({'message': 'Logout successful'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
