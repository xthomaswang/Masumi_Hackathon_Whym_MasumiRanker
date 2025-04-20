// src/pages/category.jsx
import React, { useState, useEffect, useMemo } from 'react'; // Added useState, useEffect, useMemo
import { useParams } from "react-router-dom";
import { useAgentsContext } from '../context';
import Agents from '../component/agents'; // For the main list
import HorizontalAgentList from '../component/HorizontalAgentList'; // For the horizontal list of recommendations
import apiClient from '../api/axiosInstance'; // For API calls
import axios from 'axios';                     // For isCancel

const Category = () => {
  const { tag } = useParams(); // Category slug from URL
  const { agents: allAgents, loading: agentsLoading, error: agentsError } = useAgentsContext(); // Main agent list from context

  // --- State for Category-Specific Recommendations ---
  const [recommendedAgents, setRecommendedAgents] = useState([]);
  const [recsLoading, setRecsLoading] = useState(false);
  const [recsError, setRecsError] = useState(null);

  const categoryName = useMemo(() => {
      return decodeURIComponent(tag || '').replace(/-/g, ' ');
  }, [tag]);

  // --- Effect to Fetch Category-Specific Recommendations ---
  useEffect(() => {
    // Only run if we have a category name
    if (!categoryName) return;

    const controller = new AbortController();
    const signal = controller.signal;

    const fetchCategoryRecommendations = async () => {
      setRecsLoading(true);
      setRecsError(null);
      setRecommendedAgents([]);

      try {
        // --- TODO: Replace with your actual Recommendation API details ---
        // --- ASSUMPTION: API takes category name and returns { dids: [...] } ---
        console.log(`Workspaceing recommendations for category: ${categoryName}`);
        const encodedCategory = encodeURIComponent(categoryName);
        // Example ASSUMED URL, replace with actual one!
        const recsApiUrl = `/api/recommendations?category=${encodedCategory}`;

        const recsResponse = await apiClient.get(recsApiUrl, { signal });

        if (recsResponse.data && Array.isArray(recsResponse.data.dids) && recsResponse.data.dids.length > 0) {
          const recommendedDids = recsResponse.data.dids;

          // --- Now fetch full details for these DIDs ---
          // NOTE: This assumes you want full details. Adjust if API returns enough info directly.
          // ALSO NOTE: This uses ID. If your recommendations use DID, you might need an endpoint to fetch by DID or match ID from context.
          // Let's assume for now we match by ID if possible, or fetch by ID.
          // FINDING BY ID in context (Faster if applicable):
          const recsDidSet = new Set(recommendedDids); // If API returns DIDs
          const foundAgents = allAgents.filter(agent => agent.did && recsDidSet.has(agent.did));
          // TODO: Decide if finding in context is enough, or if separate GET /api/agents/{id} calls are needed like in Modal.
          // For simplicity now, let's assume finding in context is okay IF the recs API returns DIDs matching context agents.
          // A more robust way is fetching by ID like in Modal if context might be incomplete.
          console.log("Found recommended agents in context:", foundAgents);
          setRecommendedAgents(foundAgents); // Using agents found in context for now

          // --- Placeholder for Fetching details by ID (like Modal) if needed ---
          /*
          const detailPromises = recommendedDids.map(did => ??? ); // Need agent ID from DID or fetch by DID
          // const fetchedFullDetails = await Promise.all(detailPromises);
          // const successfulAgents = fetchedFullDetails.filter(a => a && !a.error);
          // setRecommendedAgents(successfulAgents);
          */
          // --- End Placeholder ---

        } else {
          // No recommendations returned or unexpected format
           setRecommendedAgents([]); // Ensure it's empty
        }
        // --- End API Call ---

      } catch (err) {
        if (axios.isCancel(err)) {
          console.log('Category recommendations fetch cancelled');
        } else if (!signal.aborted) {
          console.error("Error fetching category recommendations:", err);
          setRecsError(err.message || "Could not load recommendations.");
          setRecommendedAgents([]);
        }
      } finally {
        if (!signal.aborted) setRecsLoading(false);
      }
    };

    fetchCategoryRecommendations();

    return () => controller.abort();

  }, [categoryName, allAgents]); // Re-run if categoryName changes, or if allAgents list updates

  // --- Filter and Sort main list (same as before) ---
  const filteredAgents = useMemo(() => {
      if (agentsLoading || !allAgents) return [];
      return allAgents.filter(agent =>
          agent && agent.category && agent.category.toLowerCase() === categoryName.toLowerCase()
      );
  }, [agentsLoading, allAgents, categoryName]);

  const sortedAgents = useMemo(() => {
      return [...filteredAgents].sort((a, b) => (b.avg_score || 0) - (a.avg_score || 0));
  }, [filteredAgents]);

  // --- Main Render ---
  if (agentsLoading) return <div>Loading category agents...</div>;
  if (agentsError) return <div style={{ color: 'red' }}>Error loading data: {agentsError}</div>;

  return (
    <div className="category-page">
      <h1 className="category-title">Category: {categoryName}</h1>
      <p className="category-description">The following is the ranking for {categoryName}.</p>
       
      


      <h3 className="category-subheading">Top Rank AI Agents</h3>
      <div className="agents-container-wrapper">
        {sortedAgents.length > 0 ? (
          <Agents agents={sortedAgents} />
        ) : (
          <p>No agents found in the '{categoryName}' category.</p>
        )}
      </div>
    </div>
  );
};

export default Category;