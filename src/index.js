import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css'; // Optional: Include your global styles here
import App from './App';
// Optional: For measuring performance in your app
import reportWebVitals from './reportWebVitals';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// To start measuring performance, pass a function to log results (e.g. reportWebVitals(console.log))
reportWebVitals();
