import React from 'react';
import { Link } from 'react-router-dom';
// Ensure API_BASE_URL is correctly exported from axiosInstance.js
import { API_BASE_URL } from '../api/axiosInstance';

const Agents = ({ agents = [] }) => {
  return (
    <div className="agents-container">
      {agents.map((agent) => {
        let agentId = agent.id;
        if (agentId === undefined || agentId === null) {
          console.warn('Agent is missing an ID:', agent);
          agentId = Math.random().toString();
        }
        const detailPath = agent.id !== undefined ? `/detail/${agent.id}` : '#';

        // --- Format the score (same as before) ---
        const scorePercent = (typeof agent.score === 'number')
                             ? (agent.score * 100).toFixed(0)
                             : null;

        return (
          <Link
            key={agentId}
            to={detailPath}
            style={{ textDecoration: 'none', color: 'inherit', display: 'block', marginBottom: '15px' }}
            onClick={(e) => { if (detailPath === '#') e.preventDefault(); }}
          >
            {/* Use className. Removed inline position/overflow unless needed elsewhere */}
            <div className="agent-card" style={{ display: 'flex', alignItems: 'center', padding: '15px', border: '1px solid #eee', borderRadius: '8px', backgroundColor: 'rgb(250,253, 255)' /* Or use CSS */ }}>
              {/* Agent main info wrapper */}
              <div style={{ display: 'flex', alignItems: 'center', flexGrow: 1 }}>
                  {/* Left side */}
                  <div className="agent-left" style={{ display: 'flex', alignItems: 'center', flexGrow: 1, gap: '1rem' }}>
                      <div className="img">
                          <img
                              src={`${API_BASE_URL}${agent.img_url || ''}`}
                              alt={`${agent.name || 'Agent'} icon`}
                              style={{ width: '60px', height: '60px', borderRadius: '50%', objectFit: 'cover', backgroundColor: '#e0e0e0' }}
                              onError={(e) => { e.target.onerror = null; e.target.src = "/image/images.jpeg"; }}
                          />
                      </div>
                      <div className="agent-info">
                          <h4 style={{ margin: '0 0 5px 0' }}>{agent.name || 'Unnamed Agent'}</h4>
                          <p style={{ margin: '0', fontSize: '0.9em', color: '#555' }}>{agent.description || 'No description.'}</p>
                          {/* --- ADD SCORE DISPLAY HERE --- */}
                          {scorePercent !== null && (
                              <p style={{ margin: '5px 0 0 0', fontSize: '0.85em', color: '#007bff' /* Blue color for score */, fontWeight: '500' }}>
                                  Relevance Score: {scorePercent}%
                              </p>
                          )}
                          {/* --- END SCORE DISPLAY --- */}
                      </div>
                  </div>
                   {/* Right side (Rating + Price) */}
                  <div className="star-price-section" style={{ textAlign: 'right', marginLeft: '15px', flexShrink: 0 }}>
                       {/* ... Star rating and price ... */}
                        <div className="star-rate" style={{ marginBottom: '5px', whiteSpace: 'nowrap' }}>
                            {"★".repeat(Math.round(typeof agent.avg_score === 'number' ? Math.min(5, Math.max(0, agent.avg_score)) : 0)) +
                             "☆".repeat(5 - Math.round(typeof agent.avg_score === 'number' ? Math.min(5, Math.max(0, agent.avg_score)) : 0))}
                             <span style={{fontSize: '0.8em', color: '#777'}}> ({agent.num_ratings !== undefined ? agent.num_ratings : '0'})</span>
                        </div>
                        <div className="price">
                            <span style={{ fontWeight: 'bold', color: '#333' }}>${typeof agent.price_usd === 'number' ? agent.price_usd.toFixed(2) : 'N/A'}</span>
                        </div>
                  </div>
              </div>{/* End of main info wrapper */}

              {/* --- REMOVED Score Panel Div --- */}

            </div> {/* End of agent-card */}
          </Link>
        );
      })}
      {agents.length === 0 && <p>No agents to display.</p>}
    </div>
  );
};

export default Agents;