from flask import Flask, request, jsonify, send_from_directory
import cv2
import mediapipe as mp
import os
import numpy as np
import math
from werkzeug.utils import secure_filename
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Folders
UPLOAD_FOLDER = 'uploads'  # Where Node server uploads go
PROCESSED_FOLDER = 'processed_videos'
if not os.path.exists(PROCESSED_FOLDER):
    os.makedirs(PROCESSED_FOLDER)

# Mediapipe Pose
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()

# ---------- HELPER FUNCTIONS ----------

def calculate_angle(a, b, c):
    """
    Calculates the angle (in degrees) at point b given points a, b, and c.
    """
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    ba = a - b
    bc = c - b
    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    cosine_angle = np.clip(cosine_angle, -1.0, 1.0)
    angle = np.degrees(np.arccos(cosine_angle))
    return angle

def draw_line_and_label(frame, pt1, pt2, label, color=(0,255,255)):
    """
    Draws a line between pt1 and pt2 and puts a label near the midpoint.
    """
    pt1 = (int(pt1[0]), int(pt1[1]))
    pt2 = (int(pt2[0]), int(pt2[1]))
    cv2.line(frame, pt1, pt2, color, 3)
    mid_x = (pt1[0] + pt2[0]) // 2
    mid_y = (pt1[1] + pt2[1]) // 2
    cv2.putText(frame, label, (mid_x, mid_y - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

def draw_progress_bar(frame, x, y, width, height, progress, label="Progress"):
    """
    Draws a horizontal progress bar at (x, y) with given width/height and 0-100 progress.
    """
    cv2.rectangle(frame, (x, y), (x + width, y + height), (255,255,255), 2)
    fill_w = int((progress / 100) * width)
    cv2.rectangle(frame, (x, y), (x + fill_w, y + height), (0,255,0), -1)
    cv2.putText(frame, f"{label}: {progress}%", (x + width + 10, y + height - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)

def draw_radial_gauge(frame, center, radius, angle_val, label="Squat Gauge", min_angle=70, max_angle=160):
    """
    Draws a circular (radial) gauge with a 'needle' pointing to angle_val.
    The gauge arcs from min_angle to max_angle.
    """
    # 1) Draw outer circle
    cv2.circle(frame, center, radius, (255,255,255), 2)

    # 2) Map angle_val to [0..180] for the arc
    #    If knee angle = min_angle => 0 degrees in gauge
    #    If knee angle = max_angle => 180 degrees in gauge
    gauge_range = max_angle - min_angle
    normalized = (angle_val - min_angle) / gauge_range
    normalized = max(0, min(1, normalized))  # clamp 0..1
    gauge_degrees = int(normalized * 180)

    # 3) Draw color arc from 0 to gauge_degrees
    #    We'll break it down into small lines to simulate an arc
    for deg in range(0, gauge_degrees + 1, 2):
        rad = math.radians(deg + 180)  # start from bottom (180 deg offset)
        x = int(center[0] + radius * math.cos(rad))
        y = int(center[1] + radius * math.sin(rad))
        cv2.line(frame, center, (x, y), (0,255,0), 2)

    # 4) Label the gauge
    cv2.putText(frame, label, (center[0] - radius, center[1] - radius - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
    cv2.putText(frame, f"{int(angle_val)} deg", (center[0] - 30, center[1] + radius + 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

def draw_advanced_info(frame, exercise_name, sets, total_sets, counter, total_reps, stage):
    """
    Draw text overlays: exercise name, sets, reps, stage, etc.
    """
    cv2.putText(frame, f"Exercise: {exercise_name}", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
    cv2.putText(frame, f"Counter: {counter}", (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
    cv2.putText(frame, f"Sets: {sets}/{total_sets}", (20, 120),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
    cv2.putText(frame, f"Stage: {stage}", (20, 160),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)

    # Example: progress for reps
    if total_reps > 0:
        progress = int((counter / total_reps) * 100)
    else:
        progress = 0
    draw_progress_bar(frame, 20, 190, 200, 20, progress, label="Progress")

# ---------- FLASK ENDPOINTS ----------

@app.route('/process_video', methods=['POST'])
def process_video():
    """
    Receives a video or a filename, processes it, and returns analysis + processed video URL.
    We'll overlay lines, angles, radial gauge, sets, stage, etc.
    """
    if 'video' in request.files:
        video_file = request.files['video']
        filename = secure_filename(video_file.filename)
        input_video_path = os.path.join(PROCESSED_FOLDER, filename)
        video_file.save(input_video_path)
    elif 'filename' in request.form:
        filename = request.form['filename']
        input_video_path = os.path.join(UPLOAD_FOLDER, filename)
        if not os.path.exists(input_video_path):
            return jsonify({'error': 'File not found in uploads folder'}), 404
    else:
        return jsonify({'error': 'No video provided'}), 400

    cap = cv2.VideoCapture(input_video_path)
    if not cap.isOpened():
        return jsonify({'error': 'Failed to open video'}), 500

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')

    processed_filename = filename.split('.')[0] + '_processed.mp4'
    processed_video_path = os.path.join(PROCESSED_FOLDER, processed_filename)
    out = cv2.VideoWriter(processed_video_path, fourcc, fps, (width, height))

    # Example scenario
    exercise_name = "Squat"
    total_sets = 3
    current_set = 1
    total_reps = 8
    counter = 0  # how many reps so far
    stage = "Standing"

    down_threshold = 120
    up_threshold = 160
    in_down_phase = False

    # We'll track left knee + right knee angles
    left_knee_angles = []
    right_knee_angles = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb_frame)

        # Default placeholders
        left_knee_angle_val = None
        right_knee_angle_val = None

        if results.pose_landmarks:
            lm = results.pose_landmarks.landmark

            # Left leg: hip(23), knee(25), ankle(27)
            left_hip = (lm[23].x * width, lm[23].y * height)
            left_knee = (lm[25].x * width, lm[25].y * height)
            left_ankle = (lm[27].x * width, lm[27].y * height)

            left_knee_angle_val = calculate_angle(left_hip, left_knee, left_ankle)
            left_knee_angles.append(left_knee_angle_val)

            # Right leg: hip(24), knee(26), ankle(28)
            right_hip = (lm[24].x * width, lm[24].y * height)
            right_knee = (lm[26].x * width, lm[26].y * height)
            right_ankle = (lm[28].x * width, lm[28].y * height)

            right_knee_angle_val = calculate_angle(right_hip, right_knee, right_ankle)
            right_knee_angles.append(right_knee_angle_val)

            # Draw lines for left leg
            draw_line_and_label(frame, left_hip, left_knee, "")
            draw_line_and_label(frame, left_knee, left_ankle, "")
            # Label the angle near the left knee
            cv2.putText(frame, f"Angle Left: {int(left_knee_angle_val)} deg",
                        (int(left_knee[0]) + 10, int(left_knee[1]) - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2)

            # Draw lines for right leg
            draw_line_and_label(frame, right_hip, right_knee, "")
            draw_line_and_label(frame, right_knee, right_ankle, "")
            # Label the angle near the right knee
            cv2.putText(frame, f"Angle Right: {int(right_knee_angle_val)} deg",
                        (int(right_knee[0]) + 10, int(right_knee[1]) - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2)

            # Rep counting based on left knee angle (or pick right)
            knee_angle_val = left_knee_angle_val
            if knee_angle_val < down_threshold and not in_down_phase:
                in_down_phase = True
                stage = "Descent"
            elif knee_angle_val > up_threshold and in_down_phase:
                counter += 1
                in_down_phase = False
                stage = "Standing"

            # If still in down phase, guess if it's "Bottom" or "Ascent"
            if in_down_phase and knee_angle_val < 100:
                stage = "Bottom"
            elif in_down_phase and knee_angle_val >= 100:
                stage = "Ascent"

        # Draw advanced info in the top-left corner
        draw_advanced_info(
            frame,
            exercise_name=exercise_name,
            sets=current_set,
            total_sets=total_sets,
            counter=counter,
            total_reps=total_reps,
            stage=stage
        )

        # Draw a radial gauge for left knee angle (top-left or top-right)
        gauge_center = (100, 350)  # pick a location
        gauge_radius = 70
        if left_knee_angle_val is not None:
            draw_radial_gauge(frame, gauge_center, gauge_radius, left_knee_angle_val,
                              label="Squat Gauge Meter", min_angle=down_threshold, max_angle=up_threshold)

        # Display reps in bottom-left
        cv2.putText(frame, f"Reps: {counter}", (20, height - 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0,255,0), 3)

        out.write(frame)

    cap.release()
    out.release()

    # Analysis after finishing
    avg_left_knee = np.mean(left_knee_angles) if left_knee_angles else 0
    avg_right_knee = np.mean(right_knee_angles) if right_knee_angles else 0

    if counter == 0:
        squat_depth_feedback = "No reps detected. Ensure you're performing full squats."
        pace_feedback = "No rep detection to determine pace."
    else:
        if avg_left_knee > 110 or avg_right_knee > 110:
            squat_depth_feedback = "Your squat depth is shallow. Try lowering further."
        else:
            squat_depth_feedback = "Good squat depth!"
        if counter < 5:
            pace_feedback = "Slow pace detected. Consider increasing your pace."
        else:
            pace_feedback = "Good pace!"

    analysis_summary = {
        "reps": counter,
        "squat_depth": squat_depth_feedback,
        "pace": pace_feedback,
        "average_knee_angle_left": avg_left_knee,
        "average_knee_angle_right": avg_right_knee
    }

    processed_video_url = f"http://localhost:5002/download/{processed_filename}"
    return jsonify({
        "message": "Video processed successfully",
        "analysis": analysis_summary,
        "processed_video": processed_video_url
    })

@app.route('/download/<filename>')
def download_video(filename):
    return send_from_directory(PROCESSED_FOLDER, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(port=5002, debug=True)
