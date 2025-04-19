import { useState, useEffect } from "react";
import axios from "axios";
import Agents from "../component/agents";

const API_URL = process.env.REACT_APP_AGENTS_API || "https://8160-107-200-17-1.ngrok-free.app/api/agents";

const Test = () => {
    const [agents, setAgents] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        const abortController = new AbortController();
        
        const fetchAgents = async () => {
            setLoading(true);
            setError(null);
            try {
                const res = await axios.get(API_URL, {
                    headers: {
                        'ngrok-skip-browser-warning': 'true'
                    },
                    signal: abortController.signal
                });

                if (res.status >= 400) {
                    throw new Error(`HTTP error! status: ${res.status}`);
                }

                const data = res.data;
                const items = data?.items ?? data;
                
                if (Array.isArray(items)) {
                    setAgents(items);
                } else {
                    throw new Error("Unexpected data format received");
                }
            } catch (error) {
                if (abortController.signal.aborted) return;
                const errorMessage = error.response?.data?.message || error.message;
                setError(`Failed to load agents: ${errorMessage}`);
                setAgents([]);
            } finally {
                if (!abortController.signal.aborted) {
                    setLoading(false);
                }
            }
        };

        fetchAgents();
        return () => abortController.abort();
    }, []);

    if (loading) {
        return <div className="loading-indicator">Loading agents...</div>;
    }

    if (error) {
        return (
            <div className="error-message">
                <h3>Error Occurred</h3>
                <p>{error}</p>
                <button onClick={() => window.location.reload()}>Retry</button>
            </div>
        );
    }

    return (
        <div className="agents-container">
            {agents.length === 0 ? (
                <div className="empty-state">No agents available</div>
            ) : (
                <Agents agents={agents} />
            )}
        </div>
    );
};

export default Test;