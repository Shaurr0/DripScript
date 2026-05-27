import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import ErrorBoundary from './components/ErrorBoundary';
import Navigation from './components/Navigation';
import Wardrobe from './pages/Wardrobe';
import Upload from './pages/Upload';
import Outfits from './pages/Outfits';
import SavedOutfits from './pages/SavedOutfits';
import Login from './pages/Login';
import { GameProvider } from './hooks/useGame';
import { AuthProvider, useAuth } from './context/AuthContext';
import './index.css';

const AppShell = ({ children }) => (
  <div className="flex min-h-screen">
    <Navigation />
    <main className="flex-1 ml-64 bg-zinc-50 overflow-y-auto min-h-screen">{children}</main>
  </div>
);

const LoadingScreen = () => (
  <div className="min-h-screen bg-zinc-50 flex items-center justify-center">
    <div className="text-zinc-400 text-sm">Loading...</div>
  </div>
);

function ProtectedRoute({ children }) {
  const { user } = useAuth();

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

function AppRoutes() {
  const { user, loading } = useAuth();

  if (loading) {
    return <LoadingScreen />;
  }

  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to="/wardrobe" replace /> : <Login />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <AppShell>
              <Navigate to="/wardrobe" replace />
            </AppShell>
          </ProtectedRoute>
        }
      />
      <Route
        path="/wardrobe"
        element={
          <ProtectedRoute>
            <AppShell>
              <Wardrobe />
            </AppShell>
          </ProtectedRoute>
        }
      />
      <Route
        path="/upload"
        element={
          <ProtectedRoute>
            <AppShell>
              <Upload />
            </AppShell>
          </ProtectedRoute>
        }
      />
      <Route
        path="/outfits"
        element={
          <ProtectedRoute>
            <AppShell>
              <Outfits />
            </AppShell>
          </ProtectedRoute>
        }
      />
      <Route
        path="/saved"
        element={
          <ProtectedRoute>
            <AppShell>
              <SavedOutfits />
            </AppShell>
          </ProtectedRoute>
        }
      />
      <Route
        path="/recommend"
        element={
          <ProtectedRoute>
            <AppShell>
              <Navigate to="/outfits" replace />
            </AppShell>
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to={user ? '/wardrobe' : '/login'} replace />} />
    </Routes>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <GameProvider>
          <Router>
            <AppRoutes />
          </Router>
        </GameProvider>
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;
