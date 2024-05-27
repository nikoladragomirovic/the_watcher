from flask import Flask, request, jsonify, g
from pymongo import MongoClient
from minio import Minio
from datetime import datetime
from flask_cors import CORS
import bcrypt
import secrets
import string
import os
import face_recognition
import numpy as np
import cv2
from functools import wraps

app = Flask(__name__)
CORS(app, origins='*')

minio_client = Minio("127.0.0.1:9000",
                     access_key="minioadmin",
                     secret_key="minioadmin",
                     secure=False)

mongo_client = MongoClient('mongodb://localhost:27017/')
database = mongo_client['the_watcher']

def generate_session_token():
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(32))

def check_session_token(username, session_token):
    user = database['accounts'].find_one({'username': username, 'session_tokens': session_token})
    return user is not None

def get_cameras(username):
    user = database['accounts'].find_one({'username': username})
    return user.get('cameras', 'Field not found') if user else 'Field not found'

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

@app.route('/enroll', methods=['POST'])
@auth_required
def register_camera():
    camera_id = request.form.get('camera_id')
    camera_name = request.form.get('name')

    existing_camera = database['accounts'].find_one({'cameras.id': camera_id})
    if existing_camera:
        return jsonify({'message': 'Camera already registered to an account'}), 401

    user = database['accounts'].find_one({'username': g.username})
    if any(camera['id'] == camera_id for camera in user['cameras']):
        return jsonify({'message': 'Camera already registered to your account'}), 401

    result = database['accounts'].update_one(
        {'username': g.username},
        {'$push': {'cameras': {'name': camera_name, 'id': camera_id}}}
    )
    
    if result.modified_count > 0:
        return jsonify({'message': 'Camera added successfully'}), 200
    else:
        return jsonify({'message': 'Failed to add camera'}), 500


@app.route('/delete', methods=['POST'])
@auth_required
def delete_camera():
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
    
@app.route('/upload', methods=['POST'])
def upload_image():
    camera_id = request.form.get('camera_id')

    if 'image' not in request.files:
        return jsonify({'error': 'No image part'}), 400
    
    file = request.files['image']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    faces = database['accounts'].find_one({'cameras': camera_id}).get('faces', [])

    encodings = [face['encoding'] for face in faces]

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    filename = f"{timestamp}.jpg"

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
            return jsonify({'message': 'Face recognized, no need for upload'}), 200

        minio_client.put_object(camera_id, filename, file, file_size)
        return jsonify({'message': 'Image uploaded successfully', 'filename': filename}), 200
    except Exception as e:
        return str(e)
    
@app.route('/save', methods=['POST'])
@auth_required
def save_face():
    name = request.form.get('name')

    if 'photo' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['photo']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    try:
        image = face_recognition.load_image_file(file)

        face_encodings = face_recognition.face_encodings(image)

        if len(face_encodings) == 0:
            return jsonify({'error': 'No faces found in the image'}), 400

        face_encoding = face_encodings[0]

        face_encoding_list = face_encoding.tolist()

        saved_face = {"name": name, "encoding": face_encoding_list}

        if database['accounts'].find_one({'username': g.username, 'faces.name': name}) is not None:
            return jsonify({"message": "Name already exists"}), 409

        result = database['accounts'].update_one(
            {'username': g.username},
            {'$push': {'faces': saved_face}}
        )

        return jsonify({"message": "Face saved succesfully"}), 200
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
    
@app.route('/faces', methods=['POST'])
@auth_required
def get_faces():
    try:
        user = database['accounts'].find_one({'username': g.username})

        if user is None:
            return jsonify({'error': 'User not found'}), 404

        faces = user.get('faces', [])
        face_names = [face.get('name') for face in faces if 'name' in face]

        return jsonify({'face_names': face_names}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/frames', methods=['POST'])
@auth_required
def get_frames():
    cameras = get_cameras(g.username)
    data = []

    for camera in cameras:
        objects = minio_client.list_objects(str(camera), recursive=True)
        camera_object = {"name": camera, "images": []}

        for obj in objects:
            url = minio_client.presigned_get_object(str(camera), obj.object_name)
            camera_object['images'].append({"url": url, "time": obj.object_name.split('.')[0]})

        data.append(camera_object)
    
    return jsonify(data)
    
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
