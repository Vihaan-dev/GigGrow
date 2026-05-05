import React from 'react';

export default function HeaderNav({loggedUser, refreshAll, logout}){
  return (
    <header className="header">
      <div className="header-top">
        <div className="brand">
          <h1>GigShield</h1>
          <span>Safety and clarity for gig worker finances.</span>
        </div>
        <div className="toolbar">
          <nav className="nav">
            <a href="#/dashboard">Dashboard</a>
            <a href="#/manual">Manual</a>
            <a href="#/events">Events</a>
            <a href="#/chat">Chat</a>
            <a href="#/purchase">Purchase</a>
            <a href="#/schemes">Schemes</a>
          </nav>
          <div className="user-controls">
            <span>UID: {loggedUser}</span>
            <button onClick={refreshAll}>Refresh</button>
            <button onClick={logout}>Logout</button>
          </div>
        </div>
      </div>
    </header>
  );
}
