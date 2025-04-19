import React, { useState, useEffect } from 'react'; // Import useState and useEffect
import { useParams } from 'react-router-dom';
import { useAgentsContext } from '../context'; // Adjust path if necessary
import axios from 'axios'; // Import axios for making HTTP requests

// Optional: Import CSS for styling
// import './Detail.css';

// --- Base URL for the API - TODO: Move to environment variable ---
const API_BASE_URL = "https://cec0-107-200-17-1.ngrok-free.app";

const Detail = () => {
  // Get the 'id' parameter from the URL (Agent's primary ID)
  const { id } = useParams();
  // Get the main agent list context data
  const { agents, loading: agentsLoading, error: agentsError } = useAgentsContext();

  // --- State specifically for Reviews ---
  const [reviews, setReviews] = useState([]);
  const [reviewsLoading, setReviewsLoading] = useState(false); // Start as false, set true when fetching
  const [reviewsError, setReviewsError] = useState(null);

  // --- Find the current agent from the context ---
  // We memoize this calculation slightly, though not strictly necessary here
  const agent = React.useMemo(() => {
    if (agentsLoading || agentsError) return null; // Don't search if main list isn't ready/failed
    return agents.find(a => String(a.id) === id);
  }, [agents, agentsLoading, agentsError, id]);

  // --- useEffect Hook to Fetch Reviews based on agent's DID ---
  useEffect(() => {
    // Only proceed if we have found the agent and it has a 'did' property
    if (!agent?.did) {
      // If no agent or no DID, clear any existing reviews/errors (e.g., navigating from one detail page to another)
      setReviews([]);
      setReviewsLoading(false);
      setReviewsError(null);
      return; // Exit the effect
    }

    // Create an AbortController for cleanup
    const controller = new AbortController();
    const signal = controller.signal;

    const fetchReviews = async () => {
      setReviewsLoading(true);
      setReviewsError(null);
      setReviews([]); // Clear previous reviews before fetching new ones

      try {
        // URL-encode the DID for the query parameter
        const encodedDid = encodeURIComponent(agent.did);
        const apiUrl = `${API_BASE_URL}/api/ratings/by-did?did=${encodedDid}`;

        const response = await axios.get(apiUrl, {
          headers: { 'ngrok-skip-browser-warning': 'true' }, // Header for Ngrok
          signal: signal // Pass the signal to axios
        });

        // Check response structure and update state
        if (response.data && Array.isArray(response.data.items)) {
          setReviews(response.data.items);
        } else {
          // Handle unexpected response format
          console.error("Unexpected API response format for reviews:", response.data);
          setReviewsError("Received an unexpected format for reviews.");
          setReviews([]);
        }

      } catch (err) {
        // Ignore abort errors
        if (axios.isCancel(err)) {
          console.log('Review fetch cancelled');
          return;
        }
        // Handle other errors
        console.error("Error fetching reviews:", err);
        const msg = err.response?.data?.message || err.message || 'Failed to fetch reviews.';
        setReviewsError(msg);
        setReviews([]); // Clear reviews on error
      } finally {
        // Only set loading to false if the request wasn't aborted
        // Note: Axios cancellation throws an error, so this check might be redundant
        // if the catch block handles isCancel correctly, but added for clarity.
         if (!signal.aborted) {
             setReviewsLoading(false);
         }
      }
    };

    fetchReviews();

    // Cleanup function: Abort the request if component unmounts or agent.did changes
    return () => {
      controller.abort();
    };
  }, [agent?.did]); // Dependency: Re-run effect if agent.did changes


  // --- Render Helper for Stars ---
  const renderStars = (score) => {
    const roundedScore = Math.round(typeof score === 'number' ? score : 0);
    const validScore = Math.min(5, Math.max(0, roundedScore));
    return "★".repeat(validScore) + "☆".repeat(5 - validScore);
  };

  // --- Main Component Render Logic ---

  // Handle loading state for the initial agent list
  if (agentsLoading) {
    return <div style={{ padding: '20px' }}>Loading agent details...</div>;
  }

  // Handle error state for the initial agent list
  if (agentsError) {
    return <div style={{ color: 'red', padding: '20px' }}>Error loading agent data: {agentsError}</div>;
  }

  // Handle case where agent wasn't found in the list
  if (!agent) {
    return (
      <div style={{ padding: '20px' }}>
        <h2>Agent Not Found</h2>
        <p>Sorry, we couldn't find an agent with the ID: {id}</p>
      </div>
    );
  }

  // --- Render the main agent details AND the reviews section ---
  return (
    <div className="agent-detail-page" style={{ padding: '20px' }}>
      {/* --- Agent Detail Section (as before) --- */}
      <div className="agent-detail">
         {/* Agent Image */}
         {agent.img_url && (
          <img
            src={`${API_BASE_URL}${agent.img_url}`}
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
          {/* Displaying DID for reference */}
          {/* <p><strong>DID:</strong> {agent.did || 'N/A'}</p> */}
        </div>
      </div>

      {/* --- Reviews Section (Now Dynamic) --- */}
      <div className="reviews-section" style={{ marginTop: '30px' }}>
        <h3>Reviews</h3>
        {/* Conditional rendering based on reviews loading/error state */}
        {reviewsLoading && <p>Loading reviews...</p>}

        {reviewsError && <p style={{ color: 'red' }}>Error loading reviews: {reviewsError}</p>}

        {!reviewsLoading && !reviewsError && (
          reviews.length > 0 ? (
            // Map over the fetched reviews
            reviews.map((review) => (
              <div className="review" key={review.hash || review.timestamp} style={{ borderBottom: '1px dashed #ccc', paddingBottom: '15px', marginBottom: '15px' }}>
                <p><strong>Rating:</strong> {renderStars(review.score)}</p>
                <p>{review.comment || 'No comment provided.'}</p>
                <p style={{ fontSize: '0.8em', color: '#777' }}>
                  Date: {review.timestamp ? new Date(review.timestamp).toLocaleDateString() : 'N/A'}
                  {/* Display User ID if available, otherwise anonymous */}
                  {/* by {review.user_id || 'Anonymous'} */}
                </p>
              </div>
            ))
          ) : (
            // Message when loading is finished, no error, but no reviews found
            <p>No reviews available yet for this agent.</p>
          )
        )}
      </div>
    </div>
  );
}

export default Detail;