// src/context.jsx
import React, { createContext, useContext, useState, useEffect } from 'react';
// Import the configured apiClient
import apiClient from './api/axiosInstance'; // <-- Adjust path if necessary (e.g., from ./src/context/ -> ../api/axiosInstance)
// Import axios for specific checks like isCancel
import axios from 'axios';

// Create the Context
const AgentsContext = createContext();

// Provider Component
export function AgentsProvider({ children }) {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(false); // Initialize loading to false
  const [error, setError] = useState(null);

  // Effect to fetch the main list of agents once when the provider mounts
  useEffect(() => {
    // AbortController for cleanup on unmount or re-render before fetch completes
    const controller = new AbortController();
    const signal = controller.signal;

    async function fetchAgents() {
      setLoading(true); // Set loading to true right before starting the fetch
      setError(null);   // Clear any previous errors
      setAgents([]);    // Clear previous agents list

      try {
        // Use the configured apiClient to make the GET request
        // Base URL and common headers (like ngrok skip) are handled by apiClient
        const res = await apiClient.get('/api/agents?page=1&page_size=50', { // Path relative to baseURL
          signal: signal // Pass the abort signal to the request
        });

        // Process the response data
        const payload = res.data;
        // Handle potential response structures: { items: [...] } or just [...]
        const items = Array.isArray(payload?.items) ? payload.items : (Array.isArray(payload) ? payload : null);

        // Validate that we received an array of agents
        if (items !== null && Array.isArray(items)) {
          setAgents(items); // Update state with the fetched agents
        } else {
          // If the format is wrong, log it and throw an error
          console.error('Unexpected API response format for /api/agents:', payload);
          // Throwing an error here will be caught by the catch block below
          throw new Error('Received unexpected format for agent list.');
        }

      } catch (err) {
        // Check if the error was due to the request being cancelled (aborted)
        if (axios.isCancel(err) || signal.aborted) {
          console.log('Agent list fetch cancelled/aborted');
          // Don't update state if the request was cancelled
        } else {
          // Handle all other errors (network errors, server errors, format errors thrown above)
          const msg = err.message || err.response?.data?.message || 'Failed to load agents';
          console.error("Error fetching agents:", err);
          setError(msg);        // Set the error state
          setAgents([]);        // Ensure agents are cleared on error
          setLoading(false);    // Set loading to false because the fetch attempt finished (with an error)
        }
      } finally {
        // ** CORRECTED/SIMPLIFIED finally block **
        // This block runs after the try or catch finishes.
        // We ensure loading is set to false *unless* the request was aborted.
        // If an error occurred and wasn't aborted, setLoading(false) was already called in the catch block.
        // If it succeeded and wasn't aborted, this will set loading to false.
        if (!signal.aborted) {
          setLoading(false);
        }
      }
    } // end of fetchAgents function

    fetchAgents();

    // Cleanup function: This runs when the component unmounts or before the effect runs again (if dependencies change)
    return () => {
      console.log("Aborting agent fetch (context cleanup)"); // Optional: for debugging
      controller.abort(); // Abort the fetch request if it's still in progress
    };
  }, []); // Empty dependency array: This effect runs only once when the provider mounts

  // Provide the context value (state and potentially update functions) to children
  return (
    <AgentsContext.Provider value={{ agents, loading, error }}>
      {children}
    </AgentsContext.Provider>
  );
}

// Custom Hook to easily consume the context in components
export function useAgentsContext() {
  const context = useContext(AgentsContext);
  if (context === undefined) {
    // This error helps ensure components using the hook are wrapped by the provider
    throw new Error('useAgentsContext must be used within an AgentsProvider');
  }
  return context;
}