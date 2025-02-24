from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# Define an uploads folder to store video files
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return "Welcome to Gym Form Guru!"

@app.route('/upload', methods=['POST'])
def upload_video():
    # Check if the request contains a video file
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400

    file = request.files['video']
    
    # Ensure a file is selected
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Save the uploaded video file
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)
    
    # TODO: Process the video with pose estimation and rep counting logic here

    return jsonify({'message': 'Video uploaded successfully', 'file_path': file_path}), 200

if __name__ == '__main__':
    app.run(debug=True)
