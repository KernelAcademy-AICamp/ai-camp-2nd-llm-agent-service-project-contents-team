import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import ContentCreator from './pages/ContentCreator';
import ContentList from './pages/ContentList';
import Templates from './pages/Templates';
import Schedule from './pages/Schedule';
import Analytics from './pages/Analytics';
import Settings from './pages/Settings';
import CardNews from './pages/CardNews';
import './App.css';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/create" element={<ContentCreator />} />
          <Route path="/cardnews" element={<CardNews />} />
          <Route path="/contents" element={<ContentList />} />
          <Route path="/templates" element={<Templates />} />
          <Route path="/schedule" element={<Schedule />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
