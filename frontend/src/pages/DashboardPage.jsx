import { useState, useEffect } from 'react';
import { useRepos } from '../contexts/RepoContext';
import { dashboardApi } from '../api';

export default function DashboardPage({ onNavigate }) {
  const { repos } = useRepos();
  const [statsData, setStatsData] = useState({
    total_repositories: 0,
    total_chunks: 0,
    processing_repositories: 0
  });

  useEffect(() => {
    let isMounted = true;
    dashboardApi.getStats()
      .then(data => {
        if (isMounted) {
          setStatsData(data);
        }
      })
      .catch(err => {
        console.error("Failed to fetch dashboard stats:", err);
      });

    return () => {
      isMounted = false;
    };
  }, [repos]); // Fetch again if repos context changes (e.g. after adding a repo)

  const completedCount = repos.filter(r => r.status === 'completed').length;

  const stats = {
    total: statsData.total_repositories,
    completed: completedCount,
    processing: statsData.processing_repositories,
    totalChunks: statsData.total_chunks,
  };

  const quickActions = [
    {
      id: 'qa-repos',
      icon: '⟁',
      color: 'purple',
      bg: 'var(--accent-primary-glow)',
      title: 'Repositories',
      desc: 'Clone and manage your Git repositories for AI-powered code search.',
      link: 'Browse Repositories →',
      page: 'repositories',
    },
    {
      id: 'qa-search',
      icon: '⌖',
      color: 'cyan',
      bg: 'var(--accent-secondary-glow)',
      title: 'Semantic Search',
      desc: 'Find code snippets semantically across all your indexed repositories.',
      link: 'Start Searching →',
      page: 'search',
    },
    {
      id: 'qa-chat',
      icon: '◎',
      color: 'green',
      bg: 'var(--accent-success-glow)',
      title: 'AI Chat',
      desc: 'Ask questions about your codebase in natural language.',
      link: 'Open Chat →',
      page: 'chat',
    },
  ];

  return (
    <>
      {/* Top Bar */}
      <div className="topbar">
        <div>
          <div className="topbar-title">Dashboard</div>
          <div className="topbar-subtitle">Overview of your indexed repositories and vector store</div>
        </div>
        <div className="topbar-actions">
          <button
            id="dashboard-add-repo-btn"
            className="btn btn-primary btn-sm"
            onClick={() => onNavigate('repositories')}
          >
            + Add Repository
          </button>
        </div>
      </div>

      <div className="page-content">
        {/* Stats */}
        <div className="dashboard-grid">
          <div className="stat-card">
            <div className="stat-header">
              <span className="stat-label">Total Repositories</span>
              <div className="stat-icon purple">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"/>
                </svg>
              </div>
            </div>
            <div className="stat-value">{stats.total}</div>
            <div className={`stat-meta ${stats.completed > 0 ? 'positive' : ''}`}>
              {stats.completed} fully indexed
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-header">
              <span className="stat-label">Total Chunks</span>
              <div className="stat-icon cyan">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
                </svg>
              </div>
            </div>
            <div className="stat-value">{stats.totalChunks.toLocaleString()}</div>
            <div className="stat-meta">Stored in pgvector</div>
          </div>

          <div className="stat-card">
            <div className="stat-header">
              <span className="stat-label">Processing</span>
              <div className="stat-icon amber">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
                </svg>
              </div>
            </div>
            <div className="stat-value">{stats.processing}</div>
            <div className={`stat-meta ${stats.processing > 0 ? '' : ''}`}>
              {stats.processing > 0 ? 'In progress' : 'None active'}
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-header">
              <span className="stat-label">Embedding Model</span>
              <div className="stat-icon green">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>
                </svg>
              </div>
            </div>
            <div className="stat-value" style={{ fontSize: 14, letterSpacing: -0.5 }}>BGE</div>
            <div className="stat-meta">bge-small-en-v1.5 · 384d</div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="section-header">
          <div>
            <div className="section-title">Quick Actions</div>
            <div className="section-subtitle">Jump right into your workflow</div>
          </div>
        </div>
        <div className="quick-actions">
          {quickActions.map(action => (
            <div
              key={action.id}
              id={action.id}
              className="action-card"
              onClick={() => onNavigate(action.page)}
            >
              <div className="action-card-icon" style={{ background: action.bg }}>
                <span style={{ fontSize: 24, color: action.color === 'purple' ? 'var(--accent-primary-light)' : action.color === 'cyan' ? 'var(--accent-secondary)' : 'var(--accent-success)' }}>
                  {action.icon}
                </span>
              </div>
              <div className="action-card-title">{action.title}</div>
              <div className="action-card-desc">{action.desc}</div>
              <div className="action-card-link">
                {action.link} <span>→</span>
              </div>
            </div>
          ))}
        </div>

        {/* Recent Repos */}
        {repos.length > 0 && (
          <>
            <div className="section-header">
              <div>
                <div className="section-title">Recent Repositories</div>
                <div className="section-subtitle">Latest additions to your vector store</div>
              </div>
              <button className="btn btn-ghost btn-sm" onClick={() => onNavigate('repositories')}>
                View all →
              </button>
            </div>
            <div className="repo-list">
              {repos.slice(0, 3).map(repo => (
                <div key={repo.id} className="repo-card">
                  <div className="repo-icon">⟁</div>
                  <div className="repo-info">
                    <div className="repo-name">{repo.repo_name || 'Processing...'}</div>
                    <div className="repo-url">{repo.repo_url}</div>
                    <div className="repo-meta">
                      <span className={`repo-tag status-${repo.status}`}>
                        <span className={`status-dot ${repo.status === 'completed' ? 'online' : repo.status === 'processing' ? 'processing' : 'offline'}`} />
                        {repo.status}
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
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </>
  );
}
