import React from 'react';
import { Link } from 'react-router-dom';

const Agents = ({ agents = [] }) => {
  return (
    // Container for all agent cards
    <div className="agents-container">
      {/* Map over the agents array passed via props */}
      {agents.map((agent) => {
        // Ensure we have a valid ID for the key and link, fallback if needed but log warning
        let agentId = agent.id;
        if (agentId === undefined || agentId === null) {
          console.warn('Agent is missing an ID:', agent);
          agentId = Math.random().toString(); // Use a temporary random key if ID is missing (not ideal)
        }

        const detailPath = agent.id !== undefined ? `/detail/${agent.id}` : '#'; // Prevent invalid links

        return (
          // Wrap each card in a Link, using agent.id as the key
          <Link
            key={agentId} // *** Using unique agent.id for the key ***
            to={detailPath}
            style={{ textDecoration: 'none', color: 'inherit', display: 'block', marginBottom: '15px' }} // Added margin bottom
            onClick={(e) => { if (detailPath === '#') e.preventDefault(); }} // Prevent navigation if path is invalid
          >
            {/* Individual Agent Card Structure */}
            <div className="agent-card" style={{ display: 'flex', alignItems: 'center', padding: '15px', border: '1px solid #eee', borderRadius: '8px', backgroundColor: '#f0fff0' /* Light green background like image */ }}> {/* Basic styling added */}
              {/* Left side: Image + Info */}
              <div className="agent-left" style={{ display: 'flex', alignItems: 'center', flexGrow: 1 }}>
                {/* Image container */}
                <div className="img" style={{ marginRight: '15px' }}>
                  <img
                    // TODO: Consider using an environment variable for the base URL
                    src={`https://cec0-107-200-17-1.ngrok-free.app${agent.img_url || ''}`}
                    alt={`${agent.name || 'Agent'} icon`}
                    style={{ width: '60px', height: '60px', borderRadius: '50%', objectFit: 'cover', backgroundColor: '#e0e0e0' /* Placeholder bg */ }}
                    onError={(e) => {
                      e.target.onerror = null;
                      e.target.src = "/image/images.jpeg"; // Local default image path
                    }}
                  />
                </div>
                {/* Name and Description */}
                <div className="agent-info">
                  <h4 style={{ margin: '0 0 5px 0' }}>{agent.name || 'Unnamed Agent'}</h4>
                  <p style={{ margin: '0', fontSize: '0.9em', color: '#555' }}>{agent.description || 'No description.'}</p>
                </div>
              </div>

              {/* Right side: Rating + Price */}
              <div className="star-price-section" style={{ textAlign: 'right', marginLeft: '15px', flexShrink: 0 }}>
                {/* Star Rating */}
                <div className="star-rate" style={{ marginBottom: '5px', whiteSpace: 'nowrap' }}>
                  {"★".repeat(Math.round(typeof agent.avg_score === 'number' ? Math.min(5, Math.max(0, agent.avg_score)) : 0)) +
                   "☆".repeat(5 - Math.round(typeof agent.avg_score === 'number' ? Math.min(5, Math.max(0, agent.avg_score)) : 0))}
                   <span style={{fontSize: '0.8em', color: '#777'}}> ({agent.num_ratings !== undefined ? agent.num_ratings : '0'})</span> {/* Display num_ratings */}
                </div>
                {/* Price */}
                <div className="price">
                  <span style={{ fontWeight: 'bold', color: '#333' }}>${typeof agent.price_usd === 'number' ? agent.price_usd.toFixed(2) : 'N/A'}</span>
                </div>
              </div>
            </div>
          </Link>
        );
      })}
      {/* Optional: Message if no agents were passed */}
      {agents.length === 0 && <p>No agents to display.</p>}
    </div>
  );
};

export default Agents;