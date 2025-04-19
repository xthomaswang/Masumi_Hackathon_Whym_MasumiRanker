import React from 'react';

const Home = () => {
  return (
    <div
      style={{
        padding: "2rem 1rem",        // ✅ 有一点 padding 但不偏移
      }}
    >
      <h2 style={{ marginBottom: "1.5rem" }}>
        Find the Best AI Agent for Your Needs
      </h2>

      <textarea
        placeholder="Describe what you're looking for..."
        style={{
          width: "100%",             // ✅ 撑满主区域
          height: "150px",
          padding: "1rem",
          fontSize: "1.1rem",
          borderRadius: "8px",
          border: "1px solid #ccc",
          resize: "none",
          marginBottom: "1rem",
        }}
      />

      <button
        style={{
          padding: "0.6rem 1.5rem",
          fontSize: "1rem",
          borderRadius: "5px",
          border: "none",
          backgroundColor: "black",
          color: "white",
          cursor: "pointer",
        }}
      >
        Search
      </button>
    </div>
  );
};

export default Home;
