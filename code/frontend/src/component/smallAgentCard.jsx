// src/component/SmallAgentCard.jsx
import React from 'react';
import { Link } from 'react-router-dom';
import { API_BASE_URL } from '../api/axiosInstance'; // Import base URL for image

const SmallAgentCard = ({ agent }) => {
  if (!agent) return null; // Handle cases where agent data might be missing

  // Basic styles for the small card (better in CSS)
  const cardStyle = {
    border: '1px solid #eee',
    borderRadius: '8px',
    padding: '10px',
    width: '200px', // Fixed width for horizontal scrolling items
    flexShrink: 0, // Prevent cards from shrinking
    backgroundColor: '#f9f9f9',
    textAlign: 'center',
    boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
    textDecoration: 'none', // Remove underline from Link
    color: 'inherit', // Inherit text color
    display: 'flex', // Use flexbox for vertical layout
    flexDirection: 'column',
    alignItems: 'center',
    gap: '5px', // Space between elements
    transition: 'box-shadow 0.2s ease-in-out',
  };

  const imageStyle = {
    width: '50px',
    height: '50px',
    borderRadius: '50%',
    objectFit: 'cover',
    backgroundColor: '#e0e0e0',
  };

  const nameStyle = {
    fontWeight: 'bold',
    fontSize: '0.9em',
    margin: '5px 0 0 0',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    width: '100%', // Ensure text overflow works
  };

   const starStyle = {
    fontSize: '0.8em',
    color: '#666', // Lighter color for stars maybe
  };


  // Helper function for stars (can be moved to a utils file)
  const renderStars = (score) => {
      const roundedScore = Math.round(typeof score === 'number' ? score : 0);
      const validScore = Math.min(5, Math.max(0, roundedScore));
      return "★".repeat(validScore) + "☆".repeat(5 - validScore);
  };


  const detailPath = agent.id !== undefined ? `/detail/${agent.id}` : '#';

  return (
    <Link to={detailPath} style={cardStyle} className="small-agent-card"> {/* Add class for CSS */}
      <img
        src={`${API_BASE_URL}${agent.img_url || ''}`}
        alt={`${agent.name || 'Agent'} icon`}
        style={imageStyle}
        onError={(e) => { e.target.onerror = null; e.target.src = "/image/images.jpeg"; }}
      />
      <h5 style={nameStyle}>{agent.name || 'Unnamed Agent'}</h5>
      {/* Optionally add stars or price if needed */}
       <div style={starStyle}>
           {renderStars(agent.avg_score)}
           {/* Maybe add score? ({agent.num_ratings || 0}) */}
       </div>
      {/* <p>${typeof agent.price_usd === 'number' ? agent.price_usd.toFixed(2) : 'N/A'}</p> */}
    </Link>
  );
};

export default SmallAgentCard;