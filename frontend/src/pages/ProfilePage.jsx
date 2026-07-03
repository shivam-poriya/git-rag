import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { authApi } from '../api';
import { useToast } from '../contexts/ToastContext';

export default function ProfilePage() {
  const { user, setUser } = useAuth();
  const { addToast } = useToast();
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    username: '',
    email: '',
    first_name: '',
    last_name: '',
    organization_name: '',
    location: '',
    phone: '',
    birthday: '',
  });

  useEffect(() => {
    if (user) {
      setForm({
        username: user.username || '',
        email: user.email || '',
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        organization_name: user.organization_name || '',
        location: user.location || '',
        phone: user.phone || '',
        birthday: user.birthday || '',
      });
    }
  }, [user]);

  const handleChange = e => setForm(prev => ({ ...prev, [e.target.name]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.phone) { addToast('Phone number is required', 'error'); return; }
    if (!form.username) { addToast('Username is required', 'error'); return; }
    if (!form.email) { addToast('Email is required', 'error'); return; }

    setLoading(true);
    try {
      const formData = new FormData();
      Object.entries(form).forEach(([k, v]) => formData.append(k, v || ''));
      const updated = await authApi.updateProfile(formData);
      setUser(prev => ({ ...prev, ...updated }));
      addToast('Profile updated successfully!', 'success');
    } catch (err) {
      addToast(err.message || 'Failed to update profile', 'error');
    } finally {
      setLoading(false);
    }
  };

  const initials = ((form.first_name?.[0] || '') + (form.last_name?.[0] || '') || form.username?.[0] || 'U').toUpperCase();

  return (
    <>
      <div className="topbar">
        <div>
          <div className="topbar-title">Profile</div>
          <div className="topbar-subtitle">Manage your account information</div>
        </div>
      </div>

      <div className="page-content">
        <div className="profile-layout">
          {/* Profile Card */}
          <div>
            <div className="profile-card" style={{ marginBottom: 16 }}>
              <div className="profile-avatar-lg">{initials}</div>
              <div className="profile-username">{form.first_name || form.username || 'User'} {form.last_name}</div>
              <div className="profile-email">{form.email}</div>
              {form.organization_name && (
                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: -4 }}>
                  🏢 {form.organization_name}
                </div>
              )}
              {form.location && (
                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: -4 }}>
                  📍 {form.location}
                </div>
              )}
            </div>

            {/* Account Info */}
            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-lg)', padding: 18 }}>
              <div style={{ fontSize: 12, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px', color: 'var(--text-muted)', marginBottom: 12 }}>
                Account Info
              </div>
              {[
                { label: 'Username', value: `@${form.username}` },
                { label: 'Member Since', value: 'Active' },
              ].map(item => (
                <div key={item.label} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--border-subtle)' }}>
                  <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{item.label}</span>
                  <span style={{ fontSize: 12, color: 'var(--text-secondary)', fontWeight: 500 }}>{item.value}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Profile Form */}
          <div className="profile-form-card">
            <div className="section-header" style={{ marginBottom: 20 }}>
              <div>
                <div className="section-title">Edit Profile</div>
                <div className="section-subtitle">Update your personal information</div>
              </div>
            </div>

            <form className="profile-form" onSubmit={handleSubmit}>
              <div className="form-group">
                <label className="form-label" htmlFor="prof-fname">First Name</label>
                <input
                  id="prof-fname"
                  name="first_name"
                  type="text"
                  className="form-input"
                  placeholder="John"
                  value={form.first_name}
                  onChange={handleChange}
                  disabled={loading}
                />
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="prof-lname">Last Name</label>
                <input
                  id="prof-lname"
                  name="last_name"
                  type="text"
                  className="form-input"
                  placeholder="Doe"
                  value={form.last_name}
                  onChange={handleChange}
                  disabled={loading}
                />
              </div>
              <div className="form-group full">
                <label className="form-label" htmlFor="prof-username">Username *</label>
                <input
                  id="prof-username"
                  name="username"
                  type="text"
                  className="form-input"
                  value={form.username}
                  onChange={handleChange}
                  required
                  disabled={loading}
                />
              </div>
              <div className="form-group full">
                <label className="form-label" htmlFor="prof-email">Email *</label>
                <input
                  id="prof-email"
                  name="email"
                  type="email"
                  className="form-input"
                  value={form.email}
                  onChange={handleChange}
                  required
                  disabled={loading}
                />
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="prof-org">Organization</label>
                <input
                  id="prof-org"
                  name="organization_name"
                  type="text"
                  className="form-input"
                  placeholder="Company Ltd."
                  value={form.organization_name}
                  onChange={handleChange}
                  disabled={loading}
                />
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="prof-location">Location</label>
                <input
                  id="prof-location"
                  name="location"
                  type="text"
                  className="form-input"
                  placeholder="City, Country"
                  value={form.location}
                  onChange={handleChange}
                  disabled={loading}
                />
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="prof-phone">Phone *</label>
                <input
                  id="prof-phone"
                  name="phone"
                  type="tel"
                  className="form-input"
                  placeholder="+1 234 567 8900"
                  value={form.phone}
                  onChange={handleChange}
                  disabled={loading}
                />
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="prof-birthday">Birthday</label>
                <input
                  id="prof-birthday"
                  name="birthday"
                  type="date"
                  className="form-input"
                  value={form.birthday}
                  onChange={handleChange}
                  disabled={loading}
                />
              </div>

              <div style={{ gridColumn: '1 / -1', display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 8, borderTop: '1px solid var(--border-subtle)', paddingTop: 16 }}>
                <button
                  id="btn-save-profile"
                  type="submit"
                  className="btn btn-primary"
                  disabled={loading}
                >
                  {loading ? <><span className="spinner sm" /> Saving…</> : '✓ Save Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </>
  );
}
