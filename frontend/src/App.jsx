import { useState } from 'react';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ToastProvider } from './contexts/ToastContext';
import { RepoProvider } from './contexts/RepoContext';
import Sidebar from './components/Sidebar';
import AuthPage from './pages/AuthPage';
import DashboardPage from './pages/DashboardPage';
import RepositoriesPage from './pages/RepositoriesPage';
import SearchPage from './pages/SearchPage';
import ChatPage from './pages/ChatPage';
import ProfilePage from './pages/ProfilePage';

function AppShell() {
  const { user, loading } = useAuth();
  const [currentPage, setCurrentPage] = useState('dashboard');

  if (loading) {
    return (
      <div style={{
        height: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexDirection: 'column',
        gap: 16,
        background: 'var(--bg-base)',
      }}>
        <div style={{
          width: 44,
          height: 44,
          borderRadius: 10,
          background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: 20,
          fontWeight: 800,
          color: 'white',
          marginBottom: 4,
        }}>G</div>
        <span className="spinner lg" />
        <span style={{ color: 'var(--text-muted)', fontSize: 13 }}>Loading GitRAG…</span>
      </div>
    );
  }

  if (!user) return <AuthPage />;

  const pages = {
    dashboard: DashboardPage,
    repositories: RepositoriesPage,
    search: SearchPage,
    chat: ChatPage,
    profile: ProfilePage,
  };

  const PageComponent = pages[currentPage] || DashboardPage;

  return (
    <div className="app-layout">
      <Sidebar currentPage={currentPage} onNavigate={setCurrentPage} />
      <main className="main-area">
        <PageComponent onNavigate={setCurrentPage} />
      </main>
    </div>
  );
}

export default function App() {
  return (
    <ToastProvider>
      <AuthProvider>
        <RepoProvider>
          <AppShell />
        </RepoProvider>
      </AuthProvider>
    </ToastProvider>
  );
}
