// src/App.js
import React, { useState, useEffect } from "react";
import axios from "axios";

function App() {
  const [video, setVideo] = useState(null);
  const [uploadStatus, setUploadStatus] = useState("");
  const [uploadedVideos, setUploadedVideos] = useState([]);
  const [processingStatus, setProcessingStatus] = useState("");
  const [analysis, setAnalysis] = useState(null);

  useEffect(() => {
    fetchUploadedVideos();
  }, []);

  // Capture file input
  const handleFileChange = (e) => {
    setVideo(e.target.files[0]);
  };

  // Upload video to Node server
  const handleUpload = async () => {
    if (!video) {
      setUploadStatus("Please select a video file.");
      return;
    }
    const formData = new FormData();
    formData.append("video", video);
    try {
      await axios.post("http://localhost:5001/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setUploadStatus("Upload successful!");
      fetchUploadedVideos();
    } catch (error) {
      console.error(error);
      setUploadStatus("Upload failed!");
    }
  };

  // Fetch the list of uploaded videos from Node
  const fetchUploadedVideos = async () => {
    try {
      const response = await axios.get("http://localhost:5001/videos");
      setUploadedVideos(response.data);
    } catch (error) {
      console.error("Error fetching videos:", error);
    }
  };

  // Send the filename to the Python server for processing
  const handleProcessVideo = async (filename) => {
    setProcessingStatus("Processing...");
    try {
      const formData = new FormData();
      formData.append("filename", filename); // Tells Python which video to process

      const response = await axios.post("http://localhost:5002/process_video", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      setProcessingStatus("Processing complete!");
      // Save both the analysis and processed video URL in one object
      setAnalysis({
        ...response.data.analysis,
        processed_video: response.data.processed_video,
      });
    } catch (error) {
      console.error("Error processing video:", error);
      setProcessingStatus("Processing failed!");
    }
  };

  return (
    <div style={{ padding: "20px", fontFamily: "Arial, sans-serif" }}>
      <h1>Gym Form Guru</h1>
      <p>Upload your exercise video to get started:</p>

      <input type="file" accept="video/*" onChange={handleFileChange} />
      <button onClick={handleUpload} style={{ marginLeft: "10px" }}>
        Upload Video
      </button>
      <p>{uploadStatus}</p>

      <h2>Uploaded Videos</h2>
      <div>
        {uploadedVideos.length === 0 ? (
          <p>No videos uploaded yet.</p>
        ) : (
          uploadedVideos.map((vid, index) => (
            <div key={index} style={{ marginBottom: "10px" }}>
              <video width="320" height="240" controls>
                <source src={vid.url} type="video/mp4" />
              </video>
              <p>{vid.filename}</p>
              <button
                onClick={() => handleProcessVideo(vid.filename)}
                style={{
                  background: "blue",
                  color: "white",
                  padding: "5px 10px",
                  cursor: "pointer",
                  marginLeft: "10px",
                }}
              >
                Process Video
              </button>
            </div>
          ))
        )}
      </div>

      <h2>Processing Status</h2>
      <p>{processingStatus}</p>

      {analysis && (
        <div>
          <h2>Exercise Analysis</h2>
          <p>Reps: {analysis.reps}</p>
          <p>Squat Depth: {analysis.squat_depth}</p>
          <p>Pace: {analysis.pace}</p>
          <p>Average Knee Angle: {Math.round(analysis.average_knee_angle)}°</p>

          {/* Download link styled as a button */}
          <a
            href={analysis.processed_video}
            download
            style={{
              display: "inline-block",
              padding: "10px 20px",
              backgroundColor: "#007BFF",
              color: "#fff",
              textDecoration: "none",
              borderRadius: "4px",
              marginTop: "10px"
            }}
          >
            Download Processed Video
          </a>
        </div>
      )}
    </div>
  );
}

export default App;
