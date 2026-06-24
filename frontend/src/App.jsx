// gère l'affichage principal de l'application
import React, { useState, useEffect, useCallback } from 'react';
import { Toaster } from 'react-hot-toast';
import Navbar from './components/Layout/Navbar';
import ConnectionBanner from './components/Layout/ConnectionBanner';
import Sidebar from './components/Layout/Sidebar';
import ChatContainer from './components/Chat/ChatContainer';
import Dashboard from './components/IoT/Dashboard';
import AuthPage from './components/Auth/AuthPage';
import HomePage from './components/Home/HomePage';
import healthAPI from './services/api';

const HEALTH_POLL_INTERVAL_MS = 3600000;
const AUTH_STORAGE_KEY = 'msa_auth';

function App() {
  const [auth, setAuth] = useState(() => {
    try {
      const saved = localStorage.getItem(AUTH_STORAGE_KEY);
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });
  const user = auth?.user || null;

  const [activeTab, setActiveTab] = useState('home');
  const [serverStatus, setServerStatus] = useState(null);
  const [statusChecked, setStatusChecked] = useState(false);

  const [conversations, setConversations] = useState([]);
  const [isLoadingConversations, setIsLoadingConversations] = useState(false);
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  const handleAuthenticated = (loggedUser, token) => {
    const nextAuth = { user: loggedUser, token };
    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(nextAuth));
    setAuth(nextAuth);
    setActiveTab('home');
  };

  const handleLogout = () => {
    localStorage.removeItem(AUTH_STORAGE_KEY);
    setAuth(null);
    setConversations([]);
    setActiveConversationId(null);
    setActiveTab('home');
  };

  useEffect(() => {
    let cancelled = false;
    const checkHealth = async () => {
      const status = await healthAPI.getSubServersStatus();
      if (!cancelled) {
        setServerStatus(status);
        setStatusChecked(true);
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, HEALTH_POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  const refreshConversations = useCallback(async () => {
    if (!user?.id) return [];
    const list = await healthAPI.getConversations(user.id);
    setConversations(list);
    return list;
  }, [user?.id]);

  useEffect(() => {
    if (!user?.id) return;
    (async () => {
      setIsLoadingConversations(true);
      await refreshConversations();
      setIsLoadingConversations(false);
    })();
  }, [user?.id, refreshConversations]);

  const handleNewConversation = () => setActiveConversationId(null);
  const handleSelectConversation = (conversationId) => setActiveConversationId(conversationId);
  const handleConversationCreated = useCallback((conversationId) => {
    setActiveConversationId(conversationId);
    refreshConversations();
  }, [refreshConversations]);
  const handleDeleteConversation = async (conversationId) => {
    try {
      await healthAPI.deleteConversation(conversationId, user.id);
      if (conversationId === activeConversationId) setActiveConversationId(null);
      await refreshConversations();
    } catch {}
  };

  if (!user) {
    return (
      <>
        <Toaster position="top-right" />
        <AuthPage onAuthenticated={handleAuthenticated} />
      </>
    );
  }

  return (
    <div className="flex h-screen flex-col bg-gray-50">
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: { background: '#1f2937', color: '#fff', fontSize: '0.875rem' },
          success: { duration: 3000, iconTheme: { primary: '#22c55e', secondary: '#fff' } },
          error: { duration: 6000, iconTheme: { primary: '#ef4444', secondary: '#fff' } },
        }}
      />

      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        serverStatus={serverStatus}
        user={user}
        onLogout={handleLogout}
      />
      {statusChecked && <ConnectionBanner serverStatus={serverStatus} />}

      <main className="flex flex-1 overflow-hidden">
        {activeTab === 'chat' && (
          <Sidebar
            conversations={conversations}
            activeConversationId={activeConversationId}
            onSelectConversation={handleSelectConversation}
            onNewConversation={handleNewConversation}
            onDeleteConversation={handleDeleteConversation}
            isLoading={isLoadingConversations}
            isOpen={isSidebarOpen}
            onToggle={() => setIsSidebarOpen((prev) => !prev)}
          />
        )}

        <div className="flex flex-1 flex-col overflow-hidden">
          {activeTab === 'home' ? (
            <HomePage user={user} onNavigate={setActiveTab} />
          ) : activeTab === 'chat' ? (
            <ChatContainer
              user={user}
              conversationId={activeConversationId}
              onConversationCreated={handleConversationCreated}
              onConversationUpdated={refreshConversations}
              onNewConversation={handleNewConversation}
            />
          ) : (
            <Dashboard user={user} />
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
