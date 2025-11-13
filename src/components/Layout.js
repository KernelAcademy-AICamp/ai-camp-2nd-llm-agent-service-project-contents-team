import React from 'react';
import Header from './Header';
import Sidebar from './Sidebar';
import './Layout.css';

function Layout({ children }) {
  return (
    <div className="layout">
      <Header />
      <Sidebar />
      <main className="main-content">
        {children}
      </main>
    </div>
  );
}

export default Layout;
