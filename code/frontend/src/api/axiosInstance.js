// src/api/axiosInstance.js
import axios from 'axios';

// --- Define Base URL ---
// TODO: Move the fallback URL to an environment variable (.env file)
// Example .env file content: REACT_APP_API_BASE_URL=https://your-ngrok-or-deploy-url.com
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || "https://cec0-107-200-17-1.ngrok-free.app"; // Fallback

// --- Create Axios Instance ---
const apiClient = axios.create({
  baseURL: API_BASE_URL, // Base URL applied to all requests
  headers: {
    'Content-Type': 'application/json', // Default Content-Type
    'ngrok-skip-browser-warning': 'true'  // Common Ngrok header
    // Add other common headers if needed
  }
  // timeout: 10000, // Optional timeout
});

// --- Optional: Interceptors (Advanced: for global error handling, etc.) ---
// apiClient.interceptors.response.use(
//   response => response,
//   error => {
//     console.error('API Error:', error.response || error);
//     return Promise.reject(error);
//   }
// );

export default apiClient; // Export the configured instance