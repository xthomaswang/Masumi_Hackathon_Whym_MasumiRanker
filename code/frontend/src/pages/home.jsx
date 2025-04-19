import React from 'react';

const Home = () => {
  return (
    <div className="home-container">
      <h2>Find the Best AI Agent for Your Needs</h2>
      <textarea
        className="search-textarea"
        placeholder="Describe what you're looking for..."
      />
      <button className="search-button">Search</button>
    </div>
  );
};

export default Home;
