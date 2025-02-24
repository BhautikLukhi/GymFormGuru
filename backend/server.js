// server.js
const express = require('express');
const multer  = require('multer');
const cors = require('cors');
const path = require('path');
const fs = require('fs');

const app = express();
app.use(cors());
app.use(express.json()); // Allow JSON parsing

// Ensure the uploads folder exists
const uploadDir = path.join(__dirname, 'uploads');
if (!fs.existsSync(uploadDir)) {
  fs.mkdirSync(uploadDir);
}

// Serve uploaded files (so we can preview them)
app.use('/uploads', express.static(uploadDir));

// Configure Multer storage
const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, uploadDir),
  filename: (req, file, cb) => {
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
    cb(null, uniqueSuffix + '-' + file.originalname);
  }
});
const upload = multer({ storage });

// Upload endpoint
app.post('/upload', upload.single('video'), (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: 'No file received.' });
  }
  console.log(`File uploaded: ${req.file.path}`);
  res.status(200).json({ message: 'File uploaded successfully!', filename: req.file.filename });
});

// Endpoint to list uploaded videos
app.get('/videos', (req, res) => {
  fs.readdir(uploadDir, (err, files) => {
    if (err) {
      return res.status(500).json({ error: 'Error reading files' });
    }
    const videoFiles = files.map(file => ({
      filename: file,
      url: `http://localhost:5001/uploads/${file}`
    }));
    res.json(videoFiles);
  });
});

// Optional: Delete endpoint (if you want to remove videos)
app.delete('/videos/:filename', (req, res) => {
  const filename = req.params.filename;
  const filePath = path.join(uploadDir, filename);

  if (!fs.existsSync(filePath)) {
    return res.status(404).json({ error: 'File not found' });
  }

  fs.unlink(filePath, (err) => {
    if (err) {
      return res.status(500).json({ error: 'Error deleting file' });
    }
    console.log(`Deleted file: ${filename}`);
    res.status(200).json({ message: 'File deleted successfully!' });
  });
});

// Start the Node server
const PORT = process.env.PORT || 5001;
app.listen(PORT, () => {
  console.log(`Node server listening on port ${PORT}`);
});
