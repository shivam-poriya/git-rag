import { useState } from 'react';
import { useRepos } from '../contexts/RepoContext';
import { searchApi } from '../api';



export default function SearchPage() {
  const { repos } = useRepos();
  const [query, setQuery] = useState('');
  const [selectedRepo, setSelectedRepo] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [topK, setTopK] = useState('5');
  const [error, setError] = useState(null);

  const completedRepos = repos.filter(r => r.status === 'completed');

  const handleSearch = async (e) => {
    e?.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setSearched(false);
    setError(null);

    try {
      const data = await searchApi.semanticSearch(
        query.trim(),
        selectedRepo || null,
        parseInt(topK),
      );
      setResults(data);
      setSearched(true);
    } catch (err) {
      setError(err.message || 'Search failed. Please try again.');
      setResults([]);
      setSearched(true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="topbar">
        <div>
          <div className="topbar-title">Semantic Search</div>
          <div className="topbar-subtitle">Find code using natural language queries across your repositories</div>
        </div>
      </div>

      <div className="page-content">
        <form onSubmit={handleSearch}>
          <div className="search-header">
            {/* Main search input */}
            <div className="search-input-wrapper">
              <span className="search-icon-prefix">⌖</span>
              <input
                id="search-input"
                type="text"
                className="search-main-input"
                placeholder="Search your codebase… e.g. 'how are embeddings generated' or 'authentication flow'"
                value={query}
                onChange={e => setQuery(e.target.value)}
              />
            </div>

            {/* Controls */}
            <div className="search-controls">
              <select
                id="search-repo-select"
                className="search-select"
                value={selectedRepo}
                onChange={e => setSelectedRepo(e.target.value)}
                style={{ flex: 1, maxWidth: 260, background: 'var(--bg-card)', color: 'var(--text-secondary)' }}
              >
                <option value="">All Repositories</option>
                {completedRepos.map(r => (
                  <option key={r.id} value={r.id}>{r.repo_name || r.repo_url}</option>
                ))}
              </select>

              <select
                id="search-topk-select"
                className="search-select"
                value={topK}
                onChange={e => setTopK(e.target.value)}
                style={{ background: 'var(--bg-card)', color: 'var(--text-secondary)' }}
              >
                <option value="3">Top 3</option>
                <option value="5">Top 5</option>
                <option value="10">Top 10</option>
                <option value="20">Top 20</option>
              </select>

              <button
                id="btn-search-submit"
                type="submit"
                className="btn btn-primary"
                disabled={loading || !query.trim()}
              >
                {loading ? <><span className="spinner sm" /> Searching…</> : '⌖ Search'}
              </button>
            </div>
          </div>
        </form>

        {/* Results */}
        {loading && (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '60px 0', gap: 12, alignItems: 'center', color: 'var(--text-muted)' }}>
            <span className="spinner lg" />
            <span style={{ fontSize: 14 }}>Searching vector store…</span>
          </div>
        )}

        {searched && !loading && (
          <>
            {/* Error banner */}
            {error && (
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '14px 18px',
                borderRadius: 10,
                background: 'rgba(239,68,68,0.1)',
                border: '1px solid rgba(239,68,68,0.25)',
                color: '#f87171',
                fontSize: 13,
                marginBottom: 16,
              }}>
                <span style={{ fontSize: 16 }}>⚠</span>
                <span>{error}</span>
              </div>
            )}

            {!error && (
              <div className="section-header" style={{ marginBottom: 12 }}>
                <div>
                  <div className="section-title">
                    {results.length} result{results.length !== 1 ? 's' : ''} for &quot;{query}&quot;
                  </div>
                  {selectedRepo && (
                    <div className="section-subtitle">
                      in {repos.find(r => r.id === selectedRepo)?.repo_name}
                    </div>
                  )}
                </div>
              </div>
            )}

            {results.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">⌖</div>
                <div className="empty-title">No results found</div>
                <div className="empty-desc">Try a different query or add more repositories.</div>
              </div>
            ) : (
              <div className="search-results">
                {results.map((result, i) => (
                  <div key={i} id={`search-result-${i}`} className="search-result-card">
                    <div className="search-result-header">
                      <span className="search-result-file">{result.file}</span>
                      <span className="repo-tag" style={{
                        background: 'var(--bg-elevated)',
                        color: 'var(--accent-secondary)',
                        border: '1px solid rgba(6,182,212,0.2)'
                      }}>
                        {result.language}
                      </span>
                      <span className="search-result-score">
                        ✦ {(result.score * 100).toFixed(0)}% match
                      </span>
                    </div>
                    <div className="search-result-content">
                      <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
                        {result.content}
                      </pre>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {!searched && !loading && (
          <div className="empty-state" style={{ marginTop: 20 }}>
            <div className="empty-icon" style={{ opacity: 0.25 }}>⌖</div>
            <div className="empty-title">Semantic Code Search</div>
            <div className="empty-desc">
              Search using natural language. The AI understands context and meaning, not just keywords.
              Try queries like "error handling", "database connection", or "authentication middleware".
            </div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', justifyContent: 'center', marginTop: 4 }}>
              {['embedding generation', 'authentication flow', 'repository processing', 'database models'].map(hint => (
                <button
                  key={hint}
                  className="btn btn-secondary btn-sm"
                  onClick={() => { setQuery(hint); }}
                >
                  {hint}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </>
  );
}
