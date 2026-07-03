import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

export default function AuthPage() {
  const [mode, setMode] = useState('login'); // 'login' | 'register'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { login, register } = useAuth();

  const [form, setForm] = useState({
    username: '', email: '', password: '', confirmPassword: '', address: '',
  });

  const handleChange = (e) => {
    setForm(prev => ({ ...prev, [e.target.name]: e.target.value }));
    if (error) setError('');
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    if (!form.username || !form.password) { setError('Please fill in all fields.'); return; }
    setLoading(true);
    try {
      await login(form.username, form.password);
    } catch (err) {
      setError(err.message || 'Login failed. Check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    if (!form.username || !form.email || !form.password) { setError('Please fill in all required fields.'); return; }
    if (form.password !== form.confirmPassword) { setError('Passwords do not match.'); return; }
    if (form.password.length < 6) { setError('Password must be at least 6 characters.'); return; }
    setLoading(true);
    try {
      await register({ username: form.username, email: form.email, password: form.password, address: form.address });
      // Auto-login after register
      await login(form.username, form.password);
    } catch (err) {
      setError(err.message || 'Registration failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-screen">
      <div className="auth-bg-glow purple" />
      <div className="auth-bg-glow cyan" />

      <div className="auth-card">
        {/* Brand */}
        <div className="auth-brand">
          <div className="auth-brand-icon">G</div>
          <span className="auth-brand-name">GitRAG</span>
        </div>

        {/* Mode Toggle */}
        <div className="form-toggle-group" style={{ marginBottom: 24 }}>
          <button
            id="auth-tab-login"
            className={`form-toggle-btn ${mode === 'login' ? 'active' : ''}`}
            onClick={() => { setMode('login'); setError(''); }}
          >
            Sign In
          </button>
          <button
            id="auth-tab-register"
            className={`form-toggle-btn ${mode === 'register' ? 'active' : ''}`}
            onClick={() => { setMode('register'); setError(''); }}
          >
            Create Account
          </button>
        </div>

        {mode === 'login' ? (
          <>
            <h1 className="auth-title">Welcome back</h1>
            <p className="auth-subtitle">Sign in to chat with your repositories</p>
            <form className="auth-form" onSubmit={handleLogin}>
              {error && (
                <div className="auth-error">
                  <span>⚠</span> {error}
                </div>
              )}
              <div className="form-group">
                <label className="form-label" htmlFor="login-username">Username</label>
                <input
                  id="login-username"
                  name="username"
                  type="text"
                  className="form-input"
                  placeholder="your_username"
                  value={form.username}
                  onChange={handleChange}
                  autoComplete="username"
                  disabled={loading}
                />
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="login-password">Password</label>
                <input
                  id="login-password"
                  name="password"
                  type="password"
                  className="form-input"
                  placeholder="••••••••"
                  value={form.password}
                  onChange={handleChange}
                  autoComplete="current-password"
                  disabled={loading}
                />
              </div>
              <button
                id="btn-login-submit"
                type="submit"
                className="btn btn-primary w-full"
                style={{ marginTop: 4, justifyContent: 'center', padding: '11px' }}
                disabled={loading}
              >
                {loading ? <><span className="spinner sm" /> Signing in…</> : 'Sign In'}
              </button>
            </form>
            <div className="auth-switch">
              Don't have an account?{' '}
              <span className="auth-link" onClick={() => { setMode('register'); setError(''); }}>
                Create one
              </span>
            </div>
          </>
        ) : (
          <>
            <h1 className="auth-title">Get started</h1>
            <p className="auth-subtitle">Create your account to begin</p>
            <form className="auth-form" onSubmit={handleRegister}>
              {error && (
                <div className="auth-error">
                  <span>⚠</span> {error}
                </div>
              )}
              <div className="form-group">
                <label className="form-label" htmlFor="reg-username">Username *</label>
                <input
                  id="reg-username"
                  name="username"
                  type="text"
                  className="form-input"
                  placeholder="your_username"
                  value={form.username}
                  onChange={handleChange}
                  disabled={loading}
                />
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="reg-email">Email *</label>
                <input
                  id="reg-email"
                  name="email"
                  type="email"
                  className="form-input"
                  placeholder="you@example.com"
                  value={form.email}
                  onChange={handleChange}
                  disabled={loading}
                />
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="reg-password">Password *</label>
                <input
                  id="reg-password"
                  name="password"
                  type="password"
                  className="form-input"
                  placeholder="Min. 6 characters"
                  value={form.password}
                  onChange={handleChange}
                  disabled={loading}
                />
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="reg-confirm">Confirm Password *</label>
                <input
                  id="reg-confirm"
                  name="confirmPassword"
                  type="password"
                  className="form-input"
                  placeholder="••••••••"
                  value={form.confirmPassword}
                  onChange={handleChange}
                  disabled={loading}
                />
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="reg-address">Address</label>
                <input
                  id="reg-address"
                  name="address"
                  type="text"
                  className="form-input"
                  placeholder="Optional"
                  value={form.address}
                  onChange={handleChange}
                  disabled={loading}
                />
              </div>
              <button
                id="btn-register-submit"
                type="submit"
                className="btn btn-primary w-full"
                style={{ marginTop: 4, justifyContent: 'center', padding: '11px' }}
                disabled={loading}
              >
                {loading ? <><span className="spinner sm" /> Creating account…</> : 'Create Account'}
              </button>
            </form>
            <div className="auth-switch">
              Already have an account?{' '}
              <span className="auth-link" onClick={() => { setMode('login'); setError(''); }}>
                Sign in
              </span>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
