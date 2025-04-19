import React, { useState, useEffect } from 'react'; // Import useState, useEffect
import Agents from "../component/agents";         // To display the final list
import apiClient from '../api/axiosInstance';    // Import the configured Axios instance
import axios from 'axios';
// --- Styles (keep as before or move to CSS) ---
const modalOverlayStyle = { /* ... */ };
const modalContentStyle = { /* ... */ };
const closeButtonStyle = { /* ... */ };
// --- ---

// Updated Modal Component
const Modal = ({
  isOpen,
  onClose,
  searchResults, // Renamed prop: Array of basic agent info from search
  loading: searchLoading, // Loading state of the initial search
  error: searchError,     // Error state of the initial search
  query
}) => {

  // --- State for Detailed Agent Data ---
  const [detailedAgents, setDetailedAgents] = useState([]);
  const [detailsLoading, setDetailsLoading] = useState(false); // Loading state for fetching full details
  const [detailsError, setDetailsError] = useState(null);     // Error state for fetching full details

  // --- useEffect to Fetch Full Details when Search Results Arrive ---
  useEffect(() => {
    // Only run if modal is open, search isn't loading, search had no error, and we have results
    if (isOpen && !searchLoading && !searchError && searchResults && searchResults.length > 0) {
      const controller = new AbortController();
      const signal = controller.signal;

      const fetchAllDetails = async () => {
        setDetailsLoading(true);
        setDetailsError(null);
        setDetailedAgents([]); // Clear previous detailed results

        // Create an array of promises, one for each agent detail request
        const detailPromises = searchResults.map(agentBasicInfo =>
          apiClient.get(`/api/agents/${agentBasicInfo.id}`, { // Use apiClient and relative path
             signal: signal
             // No need for ngrok header here if it's in apiClient config
          }).then(response => response.data) // Extract data on success
            .catch(err => {
                // Log individual errors but don't stop Promise.allSettled
                console.error(`Failed to fetch details for agent ${agentBasicInfo.id}:`, err);
                // Return an error marker or null to indicate failure for this specific agent
                return { error: true, id: agentBasicInfo.id, message: err.message };
            })
        );

        try {
           // Wait for all promises to settle (either succeed or fail)
           // Using Promise.allSettled might be safer if one request fails
           // const results = await Promise.allSettled(detailPromises);
           // const successfulAgents = results
           //      .filter(result => result.status === 'fulfilled' && result.value && !result.value.error)
           //      .map(result => result.value);

           // Using Promise.all - simpler if you expect most to succeed
           // It will reject immediately if ANY promise fails
           const fetchedAgents = await Promise.all(detailPromises);

           // Filter out any errors marked in the catch block above (if using .catch within map)
           const successfulAgents = fetchedAgents.filter(agent => agent && !agent.error);

           setDetailedAgents(successfulAgents); // Update state with successfully fetched full agent details

           // Check if some failed
           const failedCount = fetchedAgents.length - successfulAgents.length;
           if (failedCount > 0) {
               setDetailsError(`Could not load details for ${failedCount} agent(s).`);
           }

        } catch (err) {
            // This catch block is primarily for Promise.all if one request fails hard
            if (axios.isCancel(err)) {
                 console.log('Detail fetching cancelled');
                 return;
            }
            console.error("Error fetching one or more agent details:", err);
            setDetailsError("An error occurred while loading agent details.");
            setDetailedAgents([]); // Clear results on major error
        } finally {
             if (!signal.aborted) {
                 setDetailsLoading(false);
             }
        }
      };

      fetchAllDetails();

      // Cleanup function for the effect
      return () => {
        controller.abort();
      };

    } else {
      // If modal is closed, or search is loading/error, or no search results, clear details state
      setDetailedAgents([]);
      setDetailsLoading(false);
      setDetailsError(null);
    }
  }, [isOpen, searchLoading, searchError, searchResults]); // Dependencies for the effect


  // --- Render Logic ---
  if (!isOpen) {
    return null; // Don't render if not open
  }

  // Helper function for stars
  const renderStars = (score) => { /* ... (same as before) ... */ };


  return (
    // Add className instead of style
    <div className="modal-overlay" onClick={onClose}>
      {/* Add className instead of style */}
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        {/* Add className instead of style */}
        <button className="modal-close-button" onClick={onClose}>&times;</button>

        <h3 style={{ marginTop: 0, marginBottom: '20px' }}>Recommended Agents for: "{query}"</h3>

        {/* ... (rest of the conditional rendering logic for loading, error, agents) ... */}
         {searchLoading && <p>Searching for agents...</p>}
         {searchError && <p style={{ color: 'red' }}>Error: {searchError}</p>}
         {!searchLoading && !searchError && (
           <>
             {detailsLoading && <p>Loading agent details...</p>}
             {detailsError && <p style={{ color: 'orange' }}>{detailsError}</p>}
             {!detailsLoading && (
               detailedAgents.length > 0 ? (
                 <Agents agents={detailedAgents} />
               ) : (
                 !detailsError && <p>No specific recommendations found or details could not be loaded.</p>
               )
             )}
           </>
         )}
      </div>
    </div>
  );
};

export default Modal;