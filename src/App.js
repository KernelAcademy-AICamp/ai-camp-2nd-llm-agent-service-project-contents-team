import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './pages/auth/Login';
import OAuthCallback from './pages/auth/OAuthCallback';
import DynamicOnboarding from './pages/onboarding/DynamicOnboarding';
import Home from './pages/Home';
import Dashboard from './pages/dashboard/Dashboard';
import ContentCreator from './pages/content/ContentCreator';
import ContentList from './pages/content/ContentList';
import Templates from './pages/content/Templates';
import Analytics from './pages/analytics/Analytics';
import Settings from './pages/settings/Settings';
import CardNews from './pages/content/CardNews';
import VideoCreator from './pages/content/VideoCreator';
import MyPage from './pages/profile/MyPage';
import ChatHistory from './pages/ChatHistory';
import './App.css';

function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          {/* 공개 라우트 */}
          <Route path="/login" element={<Login />} />
          <Route path="/oauth/callback" element={<OAuthCallback />} />

          {/* 온보딩 라우트 */}
          <Route
            path="/onboarding"
            element={
              <ProtectedRoute>
                <DynamicOnboarding />
              </ProtectedRoute>
            }
          />

          {/* 보호된 라우트 */}
          <Route path="/home"
            element={
              <ProtectedRoute>
                <Layout>
                  <Home />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route path="/"
            element={
              <ProtectedRoute>
                <Layout>
                  <Dashboard />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route path="/dashboard"
            element={
              <ProtectedRoute>
                <Layout>
                  <Dashboard />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/create"
            element={
              <ProtectedRoute>
                <Layout>
                  <ContentCreator />
                </Layout>
              </ProtectedRoute>
            }
          />
              
          <Route
            path="/cardnews"
            element={
              <ProtectedRoute>
                <Layout>
                  <CardNews />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/video"
            element={
              <ProtectedRoute>
                <Layout>
                  <VideoCreator />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/contents"
            element={
              <ProtectedRoute>
                <Layout>
                  <ContentList />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/templates"
            element={
              <ProtectedRoute>
                <Layout>
                  <Templates />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/analytics"
            element={
              <ProtectedRoute>
                <Layout>
                  <Analytics />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/settings"
            element={
              <ProtectedRoute>
                <Layout>
                  <Settings />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/mypage"
            element={
              <ProtectedRoute>
                <Layout>
                  <MyPage />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/chat-history"
            element={
              <ProtectedRoute>
                <Layout>
                  <ChatHistory />
                </Layout>
              </ProtectedRoute>
            }
          />

          {/* 404 페이지 */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </Router>
  );
}

export default App;
