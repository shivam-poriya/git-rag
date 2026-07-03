import { useState, useRef, useEffect, useCallback } from 'react';
import { useRepos } from '../contexts/RepoContext';
import { useToast } from '../contexts/ToastContext';
import { chatApi } from '../api';
import { marked } from 'marked';
import { useAuth } from '../contexts/AuthContext';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatTime(isoStr) {
  try {
    return new Date(isoStr).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return '';
  }
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function Message({ msg }) {
  const { user } = useAuth();
  const initials = user
    ? ((user.first_name?.[0] || '') + (user.last_name?.[0] || '') || user.username?.[0] || 'U').toUpperCase()
    : 'U';

  const getParsedMarkdown = (content) => {
    try {
      return { __html: marked.parse(content, { breaks: true, gfm: true }) };
    } catch {
      return { __html: content };
    }
  };

  return (
    <div className={`message ${msg.role}`}>
      <div className="message-avatar">
        {msg.role === 'user' ? initials : '✦'}
      </div>
      <div className="message-content">
        <div className="message-bubble" dangerouslySetInnerHTML={getParsedMarkdown(msg.content)} />
        {msg.sources && msg.sources.length > 0 && (
          <div className="message-sources">
            {msg.sources.map((src, i) => (
              <span key={i} className="source-chip">📄 {src}</span>
            ))}
          </div>
        )}
        <div className="message-time">{formatTime(msg.created_at)}</div>
      </div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="message assistant">
      <div className="message-avatar">✦</div>
      <div className="message-content">
        <div className="message-bubble" style={{ padding: '8px 14px' }}>
          <div className="typing-indicator">
            <div className="typing-dot" />
            <div className="typing-dot" />
            <div className="typing-dot" />
          </div>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function ChatPage() {
  const { repos } = useRepos();
  const { addToast } = useToast();

  const [sessions, setSessions] = useState([]);
  const [sessionsLoading, setSessionsLoading] = useState(true);
  const [activeSession, setActiveSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [input, setInput] = useState('');
  const [selectedRepo, setSelectedRepo] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [showNewModal, setShowNewModal] = useState(false);
  const [newSessionName, setNewSessionName] = useState('');
  const [creating, setCreating] = useState(false);

  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  const completedRepos = repos.filter(r => r.status === 'completed');

  // -----------------------------------------------------------------------
  // Load sessions on mount
  // -----------------------------------------------------------------------
  const loadSessions = useCallback(async () => {
    setSessionsLoading(true);
    try {
      const data = await chatApi.getSessions();
      setSessions(data);
    } catch (err) {
      addToast(err.message || 'Failed to load chat sessions', 'error');
    } finally {
      setSessionsLoading(false);
    }
  }, [addToast]);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  // -----------------------------------------------------------------------
  // Auto-scroll
  // -----------------------------------------------------------------------
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  // -----------------------------------------------------------------------
  // Create session
  // -----------------------------------------------------------------------
  const createSession = async () => {
    if (!newSessionName.trim()) {
      addToast('Please enter a chat name', 'error');
      return;
    }
    if (!selectedRepo) {
      addToast('Please select a repository', 'error');
      return;
    }

    setCreating(true);
    try {
      const session = await chatApi.createSession(newSessionName.trim(), selectedRepo);
      setSessions(prev => [session, ...prev]);
      setActiveSession(session);
      setMessages([]);
      setShowNewModal(false);
      setNewSessionName('');
      setSelectedRepo('');
    } catch (err) {
      addToast(err.message || 'Failed to create session', 'error');
    } finally {
      setCreating(false);
    }
  };

  // -----------------------------------------------------------------------
  // Select session — load message history
  // -----------------------------------------------------------------------
  const selectSession = async (session) => {
    setActiveSession(session);
    setMessages([]);
    setMessagesLoading(true);

    try {
      const msgs = await chatApi.getMessages(session.id);
      setMessages(msgs);
    } catch (err) {
      addToast(err.message || 'Failed to load messages', 'error');
    } finally {
      setMessagesLoading(false);
    }
  };

  // -----------------------------------------------------------------------
  // Send message → RAG pipeline
  // -----------------------------------------------------------------------
  const sendMessage = async () => {
    if (!input.trim() || isTyping || !activeSession) return;

    const userContent = input.trim();
    setInput('');
    setIsTyping(true);

    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    // Optimistically show the user bubble immediately
    const optimisticUser = {
      id: `opt-${Date.now()}`,
      role: 'user',
      content: userContent,
      sources: [],
      created_at: new Date().toISOString(),
    };
    setMessages(prev => [...prev, optimisticUser]);

    try {
      const result = await chatApi.sendMessage(activeSession.id, userContent);

      // Replace optimistic bubble + append assistant reply
      setMessages(prev => [
        ...prev.filter(m => m.id !== optimisticUser.id),
        result.user_message,
        result.assistant_message,
      ]);

      // Update session message count in sidebar
      setSessions(prev =>
        prev.map(s =>
          s.id === activeSession.id
            ? { ...s, message_count: (s.message_count || 0) + 2 }
            : s
        )
      );
    } catch (err) {
      // Remove optimistic bubble and show error
      setMessages(prev => prev.filter(m => m.id !== optimisticUser.id));
      addToast(err.message || 'Failed to get a response', 'error');
    } finally {
      setIsTyping(false);
    }
  };

  // -----------------------------------------------------------------------
  // Delete session
  // -----------------------------------------------------------------------
  const deleteSession = async (id, e) => {
    e.stopPropagation();
    try {
      await chatApi.deleteSession(id);
      setSessions(prev => prev.filter(s => s.id !== id));
      if (activeSession?.id === id) {
        setActiveSession(null);
        setMessages([]);
      }
    } catch (err) {
      addToast(err.message || 'Failed to delete session', 'error');
    }
  };

  // -----------------------------------------------------------------------
  // Input helpers
  // -----------------------------------------------------------------------
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleInput = (e) => {
    setInput(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
  };

  // -----------------------------------------------------------------------
  // Render
  // -----------------------------------------------------------------------
  return (
    <>
      <div className="topbar">
        <div>
          <div className="topbar-title">AI Chat</div>
          <div className="topbar-subtitle">Chat with your codebase in natural language</div>
        </div>
      </div>

      <div className="chat-layout">
        {/* Sessions Sidebar */}
        <div className="sessions-sidebar">
          <div className="sessions-header">
            <span className="sessions-title">Chats</span>
            <button
              id="btn-new-chat"
              className="btn btn-primary btn-sm"
              onClick={() => {
                setSelectedRepo('');
                setNewSessionName('');
                setShowNewModal(true);
              }}
              style={{ padding: '4px 10px', fontSize: 12 }}
            >
              + New
            </button>
          </div>

          <div className="sessions-list">
            {sessionsLoading ? (
              <div style={{ padding: '20px 12px', textAlign: 'center', color: 'var(--text-muted)', fontSize: 12 }}>
                <span className="spinner sm" /> Loading…
              </div>
            ) : sessions.length === 0 ? (
              <div style={{ padding: '20px 12px', textAlign: 'center', color: 'var(--text-muted)', fontSize: 12 }}>
                No chats yet. Click &quot;+ New&quot; to start.
              </div>
            ) : (
              sessions.map(session => (
                <div
                  key={session.id}
                  id={`session-${session.id}`}
                  className={`session-item ${activeSession?.id === session.id ? 'active' : ''}`}
                  onClick={() => selectSession(session)}
                >
                  <div className="session-name">
                    <span style={{ marginRight: 6 }}>💬</span>
                    {session.name}
                  </div>
                  <div className="session-meta">
                    <span className="session-repo">
                      {session.repo_name || 'Unknown Repo'}
                    </span>
                    <button
                      onClick={(e) => deleteSession(session.id, e)}
                      style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: 12, padding: '0 2px' }}
                      title="Delete chat"
                    >
                      ✕
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Chat Area */}
        <div className="chat-area">
          {activeSession ? (
            <>
              <div className="chat-messages">
                {messagesLoading ? (
                  <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', gap: 10, color: 'var(--text-muted)' }}>
                    <span className="spinner lg" />
                    <span style={{ fontSize: 13 }}>Loading messages…</span>
                  </div>
                ) : (
                  <>
                    {messages.length === 0 && (
                      <div className="chat-start-state">
                        <div className="chat-start-icon">✦</div>
                        <div className="chat-start-title">Ask about your code</div>
                        <div className="chat-start-desc">
                          Chatting with <strong>{activeSession.repo_name}</strong>. Ask anything — function explanations, architecture overviews, bug analysis, and more.
                        </div>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, justifyContent: 'center', marginTop: 8 }}>
                          {[
                            'Explain the main architecture',
                            'How does authentication work?',
                            'How are embeddings generated?',
                          ].map(q => (
                            <button
                              key={q}
                              className="btn btn-secondary btn-sm"
                              onClick={() => { setInput(q); textareaRef.current?.focus(); }}
                            >
                              {q}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                    {messages.map(msg => (
                      <Message key={msg.id} msg={msg} />
                    ))}
                    {isTyping && <TypingIndicator />}
                    <div ref={messagesEndRef} />
                  </>
                )}
              </div>

              <div className="chat-input-area">
                <div className="chat-input-container">
                  <textarea
                    id="chat-input"
                    ref={textareaRef}
                    className="chat-textarea"
                    placeholder="Ask something about your codebase… (Enter to send, Shift+Enter for newline)"
                    value={input}
                    onChange={handleInput}
                    onKeyDown={handleKeyDown}
                    rows={1}
                    disabled={isTyping || messagesLoading}
                  />
                  <button
                    id="chat-send-btn"
                    className="chat-send-btn"
                    onClick={sendMessage}
                    disabled={!input.trim() || isTyping || messagesLoading}
                    title="Send (Enter)"
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <line x1="22" y1="2" x2="11" y2="13"/>
                      <polygon points="22 2 15 22 11 13 2 9 22 2"/>
                    </svg>
                  </button>
                </div>
              </div>
            </>
          ) : (
            <div className="chat-start-state">
              <div className="chat-start-icon" style={{ fontSize: 60, opacity: 0.2 }}>💬</div>
              <div className="chat-start-title">Start a conversation</div>
              <div className="chat-start-desc">
                Select an existing chat session or create a new one to begin chatting with your repositories.
              </div>
              <button id="empty-new-chat-btn" className="btn btn-primary" onClick={() => {
                setSelectedRepo('');
                setNewSessionName('');
                setShowNewModal(true);
              }}>
                + New Chat
              </button>
            </div>
          )}
        </div>
      </div>

      {/* New Session Modal */}
      {showNewModal && (
        <div className="modal-overlay" onClick={e => e.target === e.currentTarget && setShowNewModal(false)}>
          <div className="modal" style={{ maxWidth: 400 }}>
            <div className="modal-header">
              <div>
                <div className="modal-title">New Chat</div>
                <div className="modal-subtitle">Start a new conversation session</div>
              </div>
              <button className="modal-close" onClick={() => setShowNewModal(false)}>✕</button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label className="form-label" htmlFor="new-chat-name">Chat Name</label>
                <input
                  id="new-chat-name"
                  type="text"
                  className="form-input"
                  placeholder="e.g., Auth System Review"
                  value={newSessionName}
                  onChange={e => setNewSessionName(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && createSession()}
                  autoFocus
                />
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="new-chat-repo">Repository (required)</label>
                <select
                  id="new-chat-repo"
                  className="form-input"
                  value={selectedRepo}
                  onChange={e => setSelectedRepo(e.target.value)}
                >
                  <option value="">— Select a repository —</option>
                  {completedRepos.map(r => (
                    <option key={r.id} value={r.id}>{r.repo_name || r.repo_url}</option>
                  ))}
                  {completedRepos.length === 0 && (
                    <option disabled>No indexed repositories yet</option>
                  )}
                </select>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowNewModal(false)}>Cancel</button>
              <button
                id="btn-create-chat"
                className="btn btn-primary"
                onClick={createSession}
                disabled={creating}
              >
                {creating ? <><span className="spinner sm" /> Creating…</> : 'Create Chat'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
