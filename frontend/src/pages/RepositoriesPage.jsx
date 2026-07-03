import { useState } from 'react';
import { repoApi } from '../api';
import { useRepos } from '../contexts/RepoContext';
import { useToast } from '../contexts/ToastContext';

function AddRepoModal({ onClose }) {
  const { addRepo, updateRepo } = useRepos();
  const { addToast } = useToast();
  const [type, setType] = useState('public'); // 'public' | 'private'
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({ repo_url: '', branch_name: '', token: '' });

  const handleChange = e => setForm(prev => ({ ...prev, [e.target.name]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.repo_url.trim()) return;
    setLoading(true);
    try {
      let resp;
      if (type === 'public') {
        resp = await repoApi.clonePublic(form.repo_url.trim(), form.branch_name.trim() || null);
      } else {
        if (!form.token.trim()) { addToast('Token is required for private repos', 'error'); setLoading(false); return; }
        resp = await repoApi.clonePrivate(form.repo_url.trim(), form.token.trim(), form.branch_name.trim() || null);
      }

      const newRepo = {
        id: resp.repo_id,
        repo_url: form.repo_url.trim(),
        repo_name: 'Processing...',
        branch_name: form.branch_name.trim() || null,
        status: 'processing',
        total_files: 0,
        total_chunks: 0,
        created_at: new Date().toISOString(),
      };

      addRepo(newRepo);
      addToast('Repository queued for processing!', 'success');
      onClose();

      // Poll status after a delay
      setTimeout(() => {
        updateRepo(resp.repo_id, { status: 'processing' });
      }, 1000);

    } catch (err) {
      addToast(err.message || 'Failed to clone repository', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-header">
          <div>
            <div className="modal-title">Add Repository</div>
            <div className="modal-subtitle">Clone and index a Git repository</div>
          </div>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        <form className="modal-body" onSubmit={handleSubmit}>
          {/* Public / Private toggle */}
          <div className="form-toggle-group">
            <button
              type="button"
              id="repo-type-public"
              className={`form-toggle-btn ${type === 'public' ? 'active' : ''}`}
              onClick={() => setType('public')}
            >
              🌐 Public
            </button>
            <button
              type="button"
              id="repo-type-private"
              className={`form-toggle-btn ${type === 'private' ? 'active' : ''}`}
              onClick={() => setType('private')}
            >
              🔒 Private
            </button>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="modal-repo-url">Repository URL *</label>
            <input
              id="modal-repo-url"
              name="repo_url"
              type="url"
              className="form-input mono"
              placeholder="https://github.com/user/repo.git"
              value={form.repo_url}
              onChange={handleChange}
              required
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="modal-branch">Branch Name</label>
            <input
              id="modal-branch"
              name="branch_name"
              type="text"
              className="form-input"
              placeholder="main (optional)"
              value={form.branch_name}
              onChange={handleChange}
              disabled={loading}
            />
            <div className="form-hint">Leave empty to use default branch</div>
          </div>

          {type === 'private' && (
            <div className="form-group">
              <label className="form-label" htmlFor="modal-token">Access Token *</label>
              <input
                id="modal-token"
                name="token"
                type="password"
                className="form-input mono"
                placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
                value={form.token}
                onChange={handleChange}
                disabled={loading}
              />
              <div className="form-hint">GitHub Personal Access Token with repo scope</div>
            </div>
          )}

          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose} disabled={loading}>Cancel</button>
            <button
              id="modal-submit-repo"
              type="submit"
              className="btn btn-primary"
              disabled={loading}
            >
              {loading ? <><span className="spinner sm" /> Cloning…</> : '⟁ Clone Repository'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function RepositoriesPage() {
  const { repos, removeRepo } = useRepos();
  const { addToast } = useToast();
  const [showModal, setShowModal] = useState(false);
  const [filter, setFilter] = useState('all');

  const filtered = filter === 'all' ? repos : repos.filter(r => r.status === filter);

  const handleDelete = async (id) => {
    const repo = repos.find(r => r.id === id);
    const repoName = repo ? (repo.repo_name || repo.repo_url) : 'this repository';
    
    if (window.confirm(`Are you sure you want to permanently delete "${repoName}"? This will delete all its indexed data and cannot be undone.`)) {
      try {
        await repoApi.deleteRepo(id);
        removeRepo(id);
        addToast('Repository deleted successfully', 'success');
      } catch (err) {
        addToast(err.message || 'Failed to delete repository', 'error');
      }
    }
  };

  const formatDate = (iso) => {
    if (!iso) return '';
    return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  return (
    <>
      <div className="topbar">
        <div>
          <div className="topbar-title">Repositories</div>
          <div className="topbar-subtitle">Manage and monitor your indexed codebases</div>
        </div>
        <div className="topbar-actions">
          <div className="form-toggle-group" style={{ padding: 2, gap: 2 }}>
            {['all', 'completed', 'processing', 'failed'].map(f => (
              <button
                key={f}
                id={`filter-${f}`}
                className={`form-toggle-btn ${filter === f ? 'active' : ''}`}
                style={{ padding: '5px 10px', fontSize: 11.5 }}
                onClick={() => setFilter(f)}
              >
                {f.charAt(0).toUpperCase() + f.slice(1)}
              </button>
            ))}
          </div>
          <button
            id="btn-add-repo"
            className="btn btn-primary btn-sm"
            onClick={() => setShowModal(true)}
          >
            + Add Repo
          </button>
        </div>
      </div>

      <div className="page-content">
        {filtered.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">⟁</div>
            <div className="empty-title">
              {filter === 'all' ? 'No repositories yet' : `No ${filter} repositories`}
            </div>
            <div className="empty-desc">
              {filter === 'all'
                ? 'Add your first Git repository to start chatting with your code using AI.'
                : `You don't have any ${filter} repositories right now.`}
            </div>
            {filter === 'all' && (
              <button id="empty-add-repo-btn" className="btn btn-primary" onClick={() => setShowModal(true)}>
                + Add Repository
              </button>
            )}
          </div>
        ) : (
          <div className="repo-list">
            {filtered.map(repo => (
              <div key={repo.id} className="repo-card">
                <div className="repo-icon">⟁</div>
                <div className="repo-info">
                  <div className="repo-name">{repo.repo_name || 'Processing...'}</div>
                  <div className="repo-url">{repo.repo_url}</div>
                  <div className="repo-meta">
                    <span className={`repo-tag status-${repo.status}`}>
                      <span className={`status-dot ${
                        repo.status === 'completed' ? 'online' :
                        repo.status === 'processing' ? 'processing' : 'offline'
                      }`} />
                      {repo.status}
                    </span>
                    {repo.branch_name && (
                      <span className="repo-tag" style={{ background: 'var(--bg-elevated)', color: 'var(--text-muted)' }}>
                        ⎇ {repo.branch_name}
                      </span>
                    )}
                    <span style={{ fontSize: 11, color: 'var(--text-muted)', marginLeft: 4 }}>
                      {formatDate(repo.created_at)}
                    </span>
                  </div>
                </div>
                <div className="repo-stats">
                  <div className="repo-stat-item">
                    <div className="repo-stat-value">{(repo.total_chunks || 0).toLocaleString()}</div>
                    <div className="repo-stat-label">Chunks</div>
                  </div>
                  <div className="repo-stat-item">
                    <div className="repo-stat-value">{repo.total_files || 0}</div>
                    <div className="repo-stat-label">Files</div>
                  </div>
                  <button
                    className="btn btn-danger btn-icon btn-sm"
                    onClick={() => handleDelete(repo.id)}
                    title="Remove from list"
                  >
                    ✕
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {showModal && <AddRepoModal onClose={() => setShowModal(false)} />}
    </>
  );
}
