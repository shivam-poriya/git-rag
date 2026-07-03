import { createContext, useContext, useState, useEffect } from 'react';
import { repoApi } from '../api';

const RepoContext = createContext(null);

export const RepoProvider = ({ children }) => {
  const [repos, setRepos] = useState([]);

  const fetchRepos = async () => {
    const token = localStorage.getItem('access_token');
    if (!token) return;
    try {
      const data = await repoApi.getRepos();
      setRepos(data);
    } catch (err) {
      console.error('Failed to load repositories from backend:', err);
    }
  };

  useEffect(() => {
    fetchRepos();
    // Poll repositories every 5 seconds to get real-time status and name updates
    const interval = setInterval(fetchRepos, 5000);
    return () => clearInterval(interval);
  }, []);

  const addRepo = (repo) => {
    setRepos(prev => [repo, ...prev]);
    fetchRepos(); // Trigger immediate update
  };

  const updateRepo = (id, updates) => {
    setRepos(prev => prev.map(r => r.id === id ? { ...r, ...updates } : r));
  };

  const removeRepo = (id) => {
    setRepos(prev => prev.filter(r => r.id !== id));
  };

  return (
    <RepoContext.Provider value={{ repos, fetchRepos, addRepo, updateRepo, removeRepo }}>
      {children}
    </RepoContext.Provider>
  );
};

export const useRepos = () => {
  const ctx = useContext(RepoContext);
  if (!ctx) throw new Error('useRepos must be used within RepoProvider');
  return ctx;
};
