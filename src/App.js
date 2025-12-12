import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ContentProvider } from './contexts/ContentContext';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './pages/auth/Login';
import OAuthCallback from './pages/auth/OAuthCallback';
import DynamicOnboarding from './pages/onboarding/DynamicOnboarding';
import Home from './pages/Home';
import Dashboard from './pages/dashboard/Dashboard';
import ContentList from './pages/content/ContentList';
import Templates from './pages/content/Templates';
import Settings from './pages/settings/Settings';
import CardNews from './pages/content/CardNews';
import ImageStudio from './pages/content/ImageStudio';
import MyPage from './pages/profile/MyPage';
import AIVideoGenerator from './pages/content/AIVideoGenerator';
import ContentHub from './pages/content/ContentHub';
import ContentCreatorSimple from './pages/content/ContentCreatorSimple';
import ContentHistory from './pages/content/ContentHistory';
import ContentEditor from './pages/content/ContentEditor';
import YouTube from './pages/connection_SNS/youtube/YouTube';
import Facebook from './pages/connection_SNS/facebook/Facebook';
import Instagram from './pages/connection_SNS/instagram/Instagram';
import X from './pages/connection_SNS/x/X';
import Threads from './pages/connection_SNS/threads/Threads';
import PrivacyPolicy from './pages/legal/PrivacyPolicy';
import DeleteData from './pages/legal/DeleteData';
import './App.css';

function App() {
  return (
    <Router>
      <AuthProvider>
        <ContentProvider>
        <Routes>
          {/* 공개 라우트 */}
          <Route path="/login" element={<Login />} />
          <Route path="/oauth/callback" element={<OAuthCallback />} />
          <Route path="/privacy" element={<PrivacyPolicy />} />
          <Route path="/delete-data" element={<DeleteData />} />

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
          <Route path="/" element={<Navigate to="/content" replace />} />
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
            path="/content"
            element={
              <ProtectedRoute>
                <Layout>
                  <ContentHub />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/create"
            element={
              <ProtectedRoute>
                <Layout>
                  <ContentCreatorSimple />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/history"
            element={
              <ProtectedRoute>
                <Layout>
                  <ContentHistory />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/editor"
            element={
              <ProtectedRoute>
                <Layout>
                  <ContentEditor />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/image-studio"
            element={
              <ProtectedRoute>
                <Layout>
                  <ImageStudio />
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
            path="/ai-video"
            element={
              <ProtectedRoute>
                <Layout>
                  <AIVideoGenerator />
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
            path="/youtube"
            element={
              <ProtectedRoute>
                <Layout>
                  <YouTube />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/facebook"
            element={
              <ProtectedRoute>
                <Layout>
                  <Facebook />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/instagram"
            element={
              <ProtectedRoute>
                <Layout>
                  <Instagram />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/x"
            element={
              <ProtectedRoute>
                <Layout>
                  <X />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/threads"
            element={
              <ProtectedRoute>
                <Layout>
                  <Threads />
                </Layout>
              </ProtectedRoute>
            }
          />

          {/* 404 페이지 */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        </ContentProvider>
      </AuthProvider>
    </Router>
  );
}

export default App;
