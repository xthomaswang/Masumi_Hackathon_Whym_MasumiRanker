// src/component/modal.jsx

import React, { useState, useEffect, useMemo } from 'react'; // Added useMemo just in case, though not strictly needed for this change
import Agents from "../component/agents";
import apiClient from '../api/axiosInstance';
import axios from 'axios';

// Styles...
const modalOverlayStyle = { /* ... */ };
const modalContentStyle = { /* ... */ };
const closeButtonStyle = { /* ... */ };

const Modal = ({
  isOpen,
  onClose,
  searchResults, // Contains objects with { id, did, name, description, score (AI score) }
  loading: searchLoading,
  error: searchError,
  query
}) => {

  const [detailedAgents, setDetailedAgents] = useState([]); // Will hold objects with full details + AI score
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [detailsError, setDetailsError] = useState(null);

  useEffect(() => {
    if (isOpen && !searchLoading && !searchError && searchResults && searchResults.length > 0) {
      const controller = new AbortController();
      const signal = controller.signal;

      const fetchAllDetails = async () => {
        setDetailsLoading(true);
        setDetailsError(null);
        setDetailedAgents([]);

        const detailPromises = searchResults.map(agentBasicInfo =>
          apiClient.get(`/api/agents/${agentBasicInfo.id}`, { signal })
            .then(response => response.data) // Gets full details (like avg_score, img_url, etc but NO AI score)
            .catch(err => {
                console.error(`Failed to fetch details for agent ${agentBasicInfo.id}:`, err);
                return { error: true, id: agentBasicInfo.id, message: err.message };
            })
        );

        try {
           const fetchedAgents = await Promise.all(detailPromises);
           // successfulAgentsBasic now contains agent objects fetched from /api/agents/{id}
           // These likely DO NOT have the AI relevance 'score' property
           const successfulAgentsBasic = fetchedAgents.filter(agent => agent && !agent.error);

           // --- !!! NEW: Merge AI relevance score from searchResults !!! ---
           // Create a lookup map from the original search results for quick access to AI scores
           const searchScoreMap = new Map();
           searchResults.forEach(result => {
               // Ensure score is a number before storing
               if (result.id && typeof result.score === 'number') {
                   searchScoreMap.set(result.id, result.score);
               }
           });

           // Map through the successfully fetched detailed agents and add the AI score
           const mergedAgents = successfulAgentsBasic.map(detailedAgent => {
               return {
                   ...detailedAgent, // Keep all fetched details (img_url, avg_score, price_usd etc.)
                   // Add the 'score' property, taking its value from the original search result via the map
                   score: searchScoreMap.get(detailedAgent.id) // Will be undefined if not found in map
               };
           });
           // --- End Merge ---

           // Now set the state with agents that have BOTH full details AND the AI score
           setDetailedAgents(mergedAgents);

           const failedCount = detailPromises.length - successfulAgentsBasic.length;
           if (failedCount > 0) {
               setDetailsError(`Could not load details for ${failedCount} agent(s).`);
           }

        } catch (err) {
            if (axios.isCancel(err)) { /*...*/ return; }
            console.error("Error fetching one or more agent details:", err);
            setDetailsError("An error occurred while loading agent details.");
            setDetailedAgents([]);
        } finally {
             if (!signal.aborted) { setDetailsLoading(false); }
        }
      };

      fetchAllDetails();
      return () => { controller.abort(); };
    } else {
      setDetailedAgents([]);
      setDetailsLoading(false);
      setDetailsError(null);
    }
    // IMPORTANT: Make sure dependencies are correct. Adding searchResults might cause re-runs if its reference changes unnecessarily.
    // Using a stringified version or just relying on isOpen/searchLoading flags might be more stable if you see infinite loops.
    // Let's try keeping it for now. If issues arise, we can reconsider.
  }, [isOpen, searchLoading, searchError, searchResults]);


  // --- Render Logic (No changes needed below this line) ---
  if (!isOpen) return null;
  const renderStars = (score) => { /* ... */ };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close-button" onClick={onClose}>&times;</button>
        <h3 style={{ marginTop: 0, marginBottom: '20px' }}>Recommended Agents for: "{query}"</h3>

         {searchLoading && <p>Searching for agents...</p>}
         {searchError && <p style={{ color: 'red' }}>Error: {searchError}</p>}
         {!searchLoading && !searchError && (
           <>
             {detailsLoading && <p>Loading agent details...</p>}
             {detailsError && <p style={{ color: 'orange' }}>{detailsError}</p>}
             {!detailsLoading && (
               detailedAgents.length > 0 ? (
                 // Agents component will now receive agents with the correct 'score' property
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