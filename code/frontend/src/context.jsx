import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

// 创建一个 Context
const AgentsContext = createContext();

// Provider 组件，用来在应用中提供全局的 agents 数据
export function AgentsProvider({ children }) {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // API 地址，可通过环境变量覆盖
  const API_URL = process.env.REACT_APP_AGENTS_API ||
    'https://cec0-107-200-17-1.ngrok-free.app/api/agents';

  useEffect(() => {
    const controller = new AbortController();

    async function fetchAgents() {
      setLoading(true);
      setError(null);
      try {
        const res = await axios.get(API_URL, {
          headers: { 'ngrok-skip-browser-warning': 'true' },
          signal: controller.signal
        });
        const payload = res.data;
        const items = Array.isArray(payload.items) ? payload.items : payload;
        if (Array.isArray(items)) {
          setAgents(items);
        } else {
          throw new Error('Unexpected API response format');
        }
      } catch (err) {
        if (!controller.signal.aborted) {
          const msg = err.response?.data?.message || err.message;
          setError(msg);
          setAgents([]);
        }
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }

    fetchAgents();
    return () => controller.abort();
  }, [API_URL]);

  return (
    <AgentsContext.Provider value={{ agents, loading, error }}>
      {children}
    </AgentsContext.Provider>
  );
}

// 自定义 Hook，方便在组件中使用 context
export function useAgentsContext() {
  const context = useContext(AgentsContext);
  if (context === undefined) {
    throw new Error('useAgentsContext 必须在 AgentsProvider 内使用');
  }
  return context;
}
