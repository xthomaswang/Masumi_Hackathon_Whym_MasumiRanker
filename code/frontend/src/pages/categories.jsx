import React, { useState, useEffect, useMemo } from 'react';
import Agents from "../component/agents"; // Your component to display a list of agents
import { useAgentsContext } from '../context'; // Context for main agent list
import { Link } from 'react-router-dom';    // For navigation links
import axios from 'axios';                  // For fetching data

// Optional: Import CSS for styling components like .categories-tag
// import './Categories.css';

// --- Configuration ---
// TODO: Move API Base URL to an environment variable (.env file) for better deployment
const API_BASE_URL = "https://cec0-107-200-17-1.ngrok-free.app";

const Categories = () => {
  // --- State and Context ---
  // Get main agent list, loading, and error states from context
  const { agents, loading: agentsLoading, error: agentsError } = useAgentsContext();

  // State specifically for fetching the list of recommended agent DIDs
  const [recommendedDids, setRecommendedDids] = useState([]);
  const [recommendationsLoading, setRecommendationsLoading] = useState(true); // Assume loading starts immediately
  const [recommendationsError, setRecommendationsError] = useState(null);

  // --- Effects ---
  // Fetch the list of recommended DIDs when the component mounts
  useEffect(() => {
    const controller = new AbortController(); // To cancel fetch if component unmounts
    const signal = controller.signal;

    const fetchRecommendations = async () => {
      // Reset state before fetching
      setRecommendationsLoading(true);
      setRecommendationsError(null);
      setRecommendedDids([]);

      try {
        const apiUrl = `${API_BASE_URL}/api/recommendations`;
        const response = await axios.get(apiUrl, {
          headers: { 'ngrok-skip-browser-warning': 'true' }, // Header for Ngrok development
          signal: signal // Pass signal for cancellation
        });

        // Validate the structure of the response
        if (response.data && Array.isArray(response.data.dids)) {
          setRecommendedDids(response.data.dids); // Store the array of DIDs
        } else {
          console.error("Unexpected API response format for recommendations:", response.data);
          setRecommendationsError("Received an unexpected format for recommendations.");
        }

      } catch (err) {
        // Ignore cancellation errors
        if (axios.isCancel(err)) {
          console.log('Recommendations fetch cancelled');
          return; // Don't update state if cancelled
        }
        // Handle other fetch errors
        console.error("Error fetching recommendations:", err);
        const msg = err.response?.data?.message || err.message || 'Failed to fetch recommendations.';
        setRecommendationsError(msg);
      } finally {
        // Ensure loading is set to false only if the request wasn't cancelled
        if (!signal.aborted) {
          setRecommendationsLoading(false);
        }
      }
    };

    fetchRecommendations();

    // Cleanup function to run when component unmounts or effect re-runs
    return () => {
      controller.abort(); // Cancel the fetch request
    };
  }, []); // Empty dependency array ensures this effect runs only once on mount

  // --- Derived Data Computations ---
  // Get unique category names from the main agent list
  const uniqueCategories = useMemo(() => {
    if (agentsLoading || !agents || agents.length === 0) return [];
    const categorySet = new Set();
    agents.forEach(agent => { if (agent?.category) categorySet.add(agent.category); });
    // The Set automatically handles uniqueness, so no duplicate keys needed for tags
    return Array.from(categorySet);
  }, [agents, agentsLoading]); // Recalculate only if agents list changes

  // Filter the main agent list to get only the recommended agents
  const recommendedAgents = useMemo(() => {
    // Wait until both main agents and recommended DIDs are loaded
    if (agentsLoading || recommendationsLoading || !agents || !recommendedDids) {
      return [];
    }
    // Use a Set for efficient checking if a DID is in the recommended list
    const didsSet = new Set(recommendedDids);
    // Return agents whose DID is present in the recommendations Set
    return agents.filter(agent => agent.did && didsSet.has(agent.did));
  }, [agents, agentsLoading, recommendedDids, recommendationsLoading]); // Recalculate if any dependency changes


  // --- Render Logic ---

  // Handle initial loading state for the main agent list
  if (agentsLoading) {
    return <div style={{ padding: '20px' }}>Loading page data...</div>;
  }

  // Handle error state for the main agent list fetch
  if (agentsError) {
    return <div style={{ color: 'red', padding: '20px' }}>Error loading page data: {agentsError}</div>;
  }

  // Render the main component structure
  return (
    <div style={{ padding: '20px' }}> {/* Added padding to main div */}
      {/* Category Tags Section */}
      <div id="categories-container" style={{ marginBottom: '30px', display: 'flex', flexWrap: 'wrap', gap: '10px' }}> {/* Using flexbox for tags */}
        {uniqueCategories.length > 0 ? (
           uniqueCategories.map((categoryName) => {
             // Create URL-friendly slug (e.g., "Code Assistant" -> "code-assistant")
             const categorySlug = categoryName.trim().toLowerCase().replace(/\s+/g, '-');
             return (
               // Link to the specific category page
               // key={categoryName} is safe because uniqueCategories contains unique names
               <Link key={categoryName} to={`/category/${categorySlug}`} style={{ textDecoration: 'none' }}>
                 {/* Apply styling via CSS class .categories-tag */}
                 <div className="categories-tag">
                   <span>{categoryName}</span>
                 </div>
               </Link>
             );
           })
        ) : (
          // Message if no categories were derived from the agent list
          <p>No categories found.</p>
        )}
      </div>

      {/* Hottest AI Agents Section */}
      <div className="recommended-agents">
        <h3>Hottest AI Agents</h3>

        {/* Display loading state for recommendations */}
        {recommendationsLoading && <p>Loading recommendations...</p>}

        {/* Display error state for recommendations */}
        {recommendationsError && <p style={{ color: 'red' }}>Could not load recommendations: {recommendationsError}</p>}

        {/* Display recommended agents or 'not found' message */}
        {!recommendationsLoading && !recommendationsError && (
          recommendedAgents.length > 0 ? (
            // Pass the filtered list to the Agents component
            <Agents agents={recommendedAgents} />
          ) : (
            // Display if loading finished without errors, but no agents matched recommendations
            <p>No specific recommendations available at this time.</p>
          )
        )}
      </div>
    </div>
  );
};

export default Categories;