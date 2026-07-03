// API service layer for GitRAG backend
const BASE_URL = 'http://localhost:8000';

const getAuthHeader = () => {
  const token = localStorage.getItem('access_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

const handleResponse = async (res) => {
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(err.detail || 'Request failed');
  }
  return res.json();
};

// Auth
export const authApi = {
  login: async (username, password) => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    const res = await fetch(`${BASE_URL}/v1/custom-auth/login/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData,
    });
    return handleResponse(res);
  },

  register: async (data) => {
    const res = await fetch(`${BASE_URL}/v1/custom-auth/register/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse(res);
  },

  getProfile: async () => {
    const res = await fetch(`${BASE_URL}/v1/custom-auth/get-user-profile/`, {
      headers: { ...getAuthHeader() },
    });
    return handleResponse(res);
  },

  updateProfile: async (formData) => {
    const res = await fetch(`${BASE_URL}/v1/custom-auth/update-user-profile/`, {
      method: 'POST',
      headers: { ...getAuthHeader() },
      body: formData,
    });
    return handleResponse(res);
  },
};

// Repository
export const repoApi = {
  clonePublic: async (repo_url, branch_name) => {
    const res = await fetch(`${BASE_URL}/v1/git-repo/repo/clone/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify({ repo_url, branch_name: branch_name || null }),
    });
    return handleResponse(res);
  },

  clonePrivate: async (repo_url, token, branch_name) => {
    const res = await fetch(`${BASE_URL}/v1/git-repo/repo/clone-private/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify({ repo_url, token, branch_name: branch_name || null }),
    });
    return handleResponse(res);
  },

  getRepos: async () => {
    const res = await fetch(`${BASE_URL}/v1/git-repo/repos/repositories`, {
      headers: { ...getAuthHeader() },
    });
    return handleResponse(res);
  },

  deleteRepo: async (repo_id) => {
    const res = await fetch(`${BASE_URL}/v1/git-repo/repos/repository/${repo_id}/`, {
      method: 'DELETE',
      headers: { ...getAuthHeader() },
    });
    if (res.status === 204) return null;
    return handleResponse(res);
  },
};

// Dashboard
export const dashboardApi = {
  getStats: async () => {
    const res = await fetch(`${BASE_URL}/v1/dashboard/stats`, {
      headers: { ...getAuthHeader() },
    });
    return handleResponse(res);
  },
};

// Semantic Search
export const searchApi = {
  semanticSearch: async (query, repo_id = null, top_k = 5) => {
    const res = await fetch(`${BASE_URL}/v1/search/semantic/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify({
        query,
        repo_id: repo_id || null,
        top_k,
      }),
    });
    return handleResponse(res);
  },
};

// Chat
export const chatApi = {
  createSession: async (name, repo_id) => {
    const res = await fetch(`${BASE_URL}/v1/chat/session/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify({ name, repo_id }),
    });
    return handleResponse(res);
  },

  getSessions: async () => {
    const res = await fetch(`${BASE_URL}/v1/chat/sessions/`, {
      headers: { ...getAuthHeader() },
    });
    return handleResponse(res);
  },

  getMessages: async (session_id) => {
    const res = await fetch(`${BASE_URL}/v1/chat/session/${session_id}/messages/`, {
      headers: { ...getAuthHeader() },
    });
    return handleResponse(res);
  },

  sendMessage: async (session_id, message) => {
    const res = await fetch(`${BASE_URL}/v1/chat/chat/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify({ session_id, message }),
    });
    return handleResponse(res);
  },

  deleteSession: async (session_id) => {
    const res = await fetch(`${BASE_URL}/v1/chat/session/${session_id}/`, {
      method: 'DELETE',
      headers: { ...getAuthHeader() },
    });
    if (res.status === 204) return null;
    return handleResponse(res);
  },
};


