// src/pages/detail.jsx
import React, { useState, useEffect, useMemo } from 'react'; // Import useMemo
import { useParams } from 'react-router-dom';
import apiClient from '../api/axiosInstance'; // Import the configured apiClient
import axios from 'axios'; // Import axios for specific checks like isCancel

// Optional: Import CSS for styling
// import './Detail.css';

const Detail = () => {
  const { id } = useParams(); // Agent ID from URL

  // --- State for Agent Details ---
  const [agent, setAgent] = useState(null);
  const [loading, setLoading] = useState(true); // Loading for main agent details
  const [error, setError] = useState(null);     // Error for main agent details

  // --- State for Reviews ---
  const [reviews, setReviews] = useState([]); // State for the raw reviews fetched
  const [reviewsLoading, setReviewsLoading] = useState(false); // Loading state specifically for reviews
  const [reviewsError, setReviewsError] = useState(null);     // Error state specifically for reviews

  // --- Effect 1: Fetch Agent Details based on ID ---
  useEffect(() => {
    if (!id) {
      setError("No agent ID provided in URL.");
      setLoading(false);
      return;
    }
    const controller = new AbortController();
    const signal = controller.signal;
    const fetchAgentDetail = async () => {
      setLoading(true);
      setError(null);
      setAgent(null);
      try {
        const response = await apiClient.get(`/api/agents/${id}`, { signal });
        if (response.data) {
          setAgent(response.data);
        } else {
          throw new Error(`No data received for agent ID: ${id}`);
        }
      } catch (err) {
        if (axios.isCancel(err) || signal.aborted) {
          console.log('Agent detail fetch cancelled/aborted');
        } else if (!signal.aborted) {
          console.error(`Error fetching details for agent ${id}:`, err);
          let errMsg = err.message || 'Failed to load agent details.';
          if (err.response && err.response.status === 404) {
            errMsg = `Sorry, we couldn't find an agent with the ID: ${id}`;
          } else {
             errMsg = err.response?.data?.message || errMsg;
          }
          setError(errMsg);
          setAgent(null);
        }
      } finally {
        if (!signal.aborted) setLoading(false);
      }
    };
    fetchAgentDetail();
    return () => controller.abort();
  }, [id]); // Re-run only if ID changes

  // --- Effect 2: Fetch Reviews based on Agent's DID (runs AFTER agent details are loaded) ---
  useEffect(() => {
    // Only proceed if we have the agent object and it has a 'did'
    if (agent?.did) {
      const controller = new AbortController();
      const signal = controller.signal;

      const fetchReviews = async () => {
        setReviewsLoading(true);
        setReviewsError(null);
        setReviews([]); // Clear previous reviews

        try {
          const encodedDid = encodeURIComponent(agent.did);
          const reviewsApiUrl = `/api/ratings/by-did?did=${encodedDid}`; // Relative path using apiClient

          const response = await apiClient.get(reviewsApiUrl, { signal });

          if (response.data && Array.isArray(response.data.items)) {
            setReviews(response.data.items); // Store the fetched reviews
          } else {
            console.error("Unexpected API response format for reviews:", response.data);
            setReviewsError("Received an unexpected format for reviews.");
            setReviews([]);
          }
        } catch (err) {
          if (axios.isCancel(err) || signal.aborted) {
            console.log('Review fetch cancelled/aborted');
          } else if (!signal.aborted) {
            console.error(`Error fetching reviews for DID ${agent.did}:`, err);
            const msg = err.response?.data?.message || err.message || 'Failed to fetch reviews.';
            setReviewsError(msg);
            setReviews([]);
          }
        } finally {
          if (!signal.aborted) setReviewsLoading(false);
        }
      };

      fetchReviews();

      // Cleanup for this effect
      return () => controller.abort();
    } else {
      // If no agent.did, ensure reviews state is cleared
      setReviews([]);
      setReviewsLoading(false);
      setReviewsError(null);
    }
  }, [agent?.did]); // Dependency: Run when agent.did becomes available/changes


  // --- Filter reviews to get unique ones based on 'hash' (like in Modal) ---
  const uniqueReviews = useMemo(() => {
    if (!reviews || reviews.length === 0) return [];
    const seenHashes = new Set();
    return reviews.filter(review => {
      if (review.hash && !seenHashes.has(review.hash)) {
        seenHashes.add(review.hash);
        return true;
      }
      return false;
    });
  }, [reviews]); // Re-filter when the raw reviews array changes

  // --- Render Helper for Stars ---
  const renderStars = (score) => {
    const roundedScore = Math.round(typeof score === 'number' ? score : 0);
    const validScore = Math.min(5, Math.max(0, roundedScore));
    return "★".repeat(validScore) + "☆".repeat(5 - validScore);
  };

  // --- Render Logic ---

  // Handle loading state for the main agent details
  if (loading) {
    return <div style={{ padding: '20px' }}>Loading agent details...</div>;
  }

  // Handle error state for fetching main agent details
  if (error) {
    return (
      <div style={{ padding: '20px' }}>
        <h2>{error.includes("couldn't find") ? "Agent Not Found" : "Error"}</h2>
        <p style={{ color: 'red' }}>{error}</p>
      </div>
    );
  }

  // Handle case where loading is done, no error, but agent is still null
  if (!agent) {
     return <div style={{ padding: '20px' }}>Agent data could not be loaded.</div>;
  }

  // Render the main agent details + the reviews section
  return (
    <div className="agent-detail-page" style={{ padding: '20px' }}>
      {/* --- Agent Detail Section --- */}
      <div className="agent-detail">
         {agent.img_url && (
          <img
             src={`${apiClient.defaults.baseURL || ''}${agent.img_url}`} // Use base URL from apiClient
             alt={`${agent.name || 'Agent'} icon`}
             style={{ width: '120px', height: '120px', borderRadius: '50%', objectFit: 'cover', marginBottom: '20px', border: '3px solid #eee' }}
             onError={(e) => { e.target.onerror = null; e.target.src = "/image/images.jpeg"; }}
           />
          )}
        <h2>{agent.name || 'Unnamed Agent'}</h2>
        <p>{agent.description || 'No description provided.'}</p>
        <div className="agent-info" style={{ margin: '20px 0', padding: '15px', border: '1px solid #ddd', borderRadius: '8px', backgroundColor: '#f9f9f9' }}>
          <p><strong>Category:</strong> {agent.category || 'N/A'}</p>
          <p>
            <strong>Rating:</strong> {renderStars(agent.avg_score)}
            ({typeof agent.avg_score === 'number' ? agent.avg_score.toFixed(1) : 'N/A'})
            ({agent.num_ratings !== undefined ? agent.num_ratings : '0'} ratings)
          </p>
          <p>
            <strong>Price:</strong> ${typeof agent.price_usd === 'number' ? agent.price_usd.toFixed(2) : 'N/A'} per hour
          </p>
        </div>
      </div>

       {/* --- Reviews Section (Now Fetches and Displays) --- */}
      <div className="reviews-section" style={{ marginTop: '30px' }}>
        <h3>Reviews</h3>
        {/* Conditional rendering based on reviews loading/error state */}
        {reviewsLoading && <p>Loading reviews...</p>}

        {reviewsError && <p style={{ color: 'red' }}>Error loading reviews: {reviewsError}</p>}

        {!reviewsLoading && !reviewsError && (
          // Use the filtered uniqueReviews array
          uniqueReviews.length > 0 ? (
            uniqueReviews.map((review) => (
              // Use review.hash as key (assuming it should be unique per entry after filtering)
              <div className="review" key={review.hash} style={{ borderBottom: '1px dashed #ccc', paddingBottom: '15px', marginBottom: '15px' }}>
                <p><strong>Rating:</strong> {renderStars(review.score)}</p>
                <p>{review.comment || 'No comment provided.'}</p>
                <p style={{ fontSize: '0.8em', color: '#777' }}>
                  Date: {review.timestamp ? new Date(review.timestamp).toLocaleDateString() : 'N/A'}
                   {/* You could add user ID if it becomes available: by {review.user_id || 'Anonymous'} */}
                </p>
              </div>
            ))
          ) : (
            // Message when loading is finished, no error, but no unique reviews found
            <p>No reviews available yet for this agent.</p>
          )
        )}
      </div>
    </div>
  );
}

export default Detail;