from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)  # ✅ Allow requests from React

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return "Welcome to Squat Form Guru!"

@app.route('/upload', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400

    file = request.files['video']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)
    
    print(f"✅ Video uploaded: {file_path}")  # Debugging log

    return jsonify({'message': 'Video uploaded successfully', 'file_path': file_path}), 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5001, debug=True)
