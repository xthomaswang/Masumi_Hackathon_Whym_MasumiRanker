import React, { useState, useEffect } from 'react'; // Removed useMemo as it's no longer needed here
import Modal from "../component/modal"; // Import the Modal component
import Agents from "../component/agents"; // Still needed for the Modal component
// NOTE: useAgentsContext might not be strictly needed *in this file* anymore
// if the only reason was filtering search results, but other parts of Home might use it.
// Keep it if needed, remove if not. Let's keep it for now just in case.
import { useAgentsContext } from '../context';
import { API_BASE_URL } from '../api/axiosInstance';

import axios from 'axios';

// TODO: Move to environment variable

const Home = () => {
  // === State Variables ===
  const [query, setQuery] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalAgents, setModalAgents] = useState([]); // Will hold agent objects from search results
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState(null);

  // Get context data - might still be needed if Home renders other things using it
  const { agents: allAgents, loading: agentsLoading, error: agentsError } = useAgentsContext();

  // === Event Handlers ===
  const handleSearch = async () => {
    if (!query.trim()) {
      alert('Please enter a search query.');
      return;
    }

    setSearchLoading(true);
    setSearchError(null);
    setModalAgents([]);
    setIsModalOpen(true);

    try {
      // --- Use the ACTUAL Search API ---
      const searchApiUrl = `${API_BASE_URL}/api/search`;
      const requestBody = {
        query: query,
        top_k: 3 // Using the default of 3 as specified, can be made dynamic later
      };

      // Use axios.post, sending requestBody as data
      const response = await axios.post(searchApiUrl, requestBody, {
        headers: {
          'ngrok-skip-browser-warning': 'true',
          'Content-Type': 'application/json' // Good practice to be explicit for POST
        }
        // Add AbortController signal if desired
      });

      // --- Process API Response (Now expects array of agent objects) ---
      if (response.data && Array.isArray(response.data.results)) {
        // Directly use the results array from the API response
        setModalAgents(response.data.results);
      } else {
        console.error("Unexpected search API response format:", response.data);
        setSearchError("Received an unexpected format from search results.");
        setModalAgents([]);
      }

    } catch (err) {
      console.error("Error during agent search:", err);
      // Handle potential 422 Validation Errors specifically if needed
      let errMsg = 'Failed to find agents.';
      if (err.response && err.response.data && err.response.data.detail) {
           // Try to format validation errors (may need adjustment based on exact detail structure)
           errMsg = `Validation Error: ${JSON.stringify(err.response.data.detail)}`;
      } else {
          errMsg = err.response?.data?.message || err.message || errMsg;
      }
      setSearchError(errMsg);
      setModalAgents([]);
    } finally {
      setSearchLoading(false);
    }
  };

  // --- Render Logic ---
  // Still might want to wait for context agents if Home displays something else from it
   if (agentsLoading) return <div>Loading initial data...</div>;
   if (agentsError) return <div style={{color: 'red'}}>Error loading initial data: {agentsError}</div>;

  return (
    <div className="home-container" style={{ padding: '20px', textAlign: 'center' }}>
      <h2>Find the Best AI Agent for Your Needs</h2>
      <textarea
        className="search-textarea"
        placeholder="Describe what you're looking for..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        style={{ width: '80%', minHeight: '100px', marginBottom: '15px', padding: '10px', border: '1px solid #ccc', borderRadius: '4px' }}
      />
      <br />
      <button
        className="search-button"
        onClick={handleSearch}
        disabled={searchLoading}
        style={{ padding: '10px 20px', cursor: 'pointer', backgroundColor: '#333', color: '#fff', border: 'none', borderRadius: '4px' }}
      >
        {searchLoading ? 'Searching...' : 'Search'}
      </button>

      {/* Render the Modal (Modal component itself doesn't need changes) */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        // *** Change prop name here ***
        searchResults={modalAgents} // Pass the basic agent objects from search API
        loading={searchLoading} // Loading state of the initial search
        error={searchError} // Error state of the initial search
        query={query}
      />
    </div>
  );
};

export default Home;