import React, { useState } from 'react';
import Sidebar from './Sidebar';
import './Layout.css';

function Layout({ children }) {
  const [isSidebarExpanded, setIsSidebarExpanded] = useState(false);

  return (
    <div className="layout">
      <Sidebar onHoverChange={setIsSidebarExpanded} />
      <main className={`main-content ${isSidebarExpanded ? 'sidebar-expanded' : ''}`}>
        {children}
      </main>
    </div>
  );
}

export default Layout;
