// src/api/axiosInstance.js
import axios from 'axios';

// --- Define Base URL ---
// TODO: Move the fallback URL to an environment variable (.env file)
// Example .env file content: REACT_APP_API_BASE_URL=https://your-ngrok-or-deploy-url.com
// vvv-- ADD 'export' Keyword Here --vvv
export const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || "https://99f0-107-200-17-1.ngrok-free.app"; // Fallback

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

// --- Optional: Interceptors ---
// ... (interceptors code if you have it) ...

export default apiClient; // Export the configured instance (this part is correct)