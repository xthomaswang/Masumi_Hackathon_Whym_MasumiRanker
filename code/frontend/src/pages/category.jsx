import React from 'react';
import { useParams } from "react-router-dom";
import { useAgentsContext } from '../context'; // Adjust path if necessary
// 1. Import the Agents component
import Agents from '../component/agents'; // <<< Use this component

// Optional: Import CSS
// import './Category.css';

const Category = () => {
  const { tag } = useParams();
  const { agents, loading, error } = useAgentsContext();

  if (loading) {
    return <div>Loading category agents...</div>;
  }

  if (error) {
    return <div style={{ color: 'red' }}>Error loading data: {error}</div>;
  }

  const categoryName = decodeURIComponent(tag || '').replace(/-/g, ' ');

  // Filter agents by category (case-insensitive)
  const filteredAgents = agents.filter(agent => {
    return agent && agent.category && agent.category.toLowerCase() === categoryName.toLowerCase();
  });

  // 2. Sort the filtered agents by 'avg_score' property, descending
  //    (Matching the star rating logic in Agents.jsx)
  const sortedAgents = [...filteredAgents].sort((a, b) => {
    // Handle potential non-numeric or missing scores
    const scoreA = typeof a.avg_score === 'number' ? a.avg_score : 0;
    const scoreB = typeof b.avg_score === 'number' ? b.avg_score : 0;
    return scoreB - scoreA; // Descending order (highest score first)
  });

  return (
    <div className="category-page">
      <h1 className="category-title">
        Category: {categoryName}
      </h1>

      <p className="category-description">
        Description of the category goes here. This category includes agents that specialize in {categoryName}.
      </p>

      <h3 className="category-subheading">Top Recommended Agents</h3>

      {/* 3. Render the Agents component, passing the sorted list */}
      <div className="agents-container-wrapper"> {/* Optional wrapper div */}
        {sortedAgents.length > 0 ? (
          // Pass the filtered and sorted agents list as a prop
          <Agents agents={sortedAgents} />
        ) : (
          <p>No agents found in the '{categoryName}' category.</p>
        )}
      </div>
    </div>
  );
};

export default Category;