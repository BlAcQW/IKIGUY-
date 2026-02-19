import React, { useEffect, useState } from 'react';

export default function AuthNavbarItem() {
  const [user, setUser] = useState<any>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const storedUser = localStorage.getItem('docs_auth_user');
    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch (e) {
        // Invalid JSON, clear it
        localStorage.removeItem('docs_auth_user');
        localStorage.removeItem('docs_auth_token');
      }
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('docs_auth_user');
    localStorage.removeItem('docs_auth_token');
    window.location.href = '/';
  };

  if (!mounted) {
    return null;
  }

  if (user) {
    return (
      <div className="navbar__item" style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
        <span style={{ fontSize: '0.9rem', color: 'var(--ifm-navbar-link-color)' }}>
          {user.email} ({user.role})
        </span>
        <button
          onClick={handleLogout}
          className="button button--sm button--outline button--primary"
          style={{ marginLeft: '0.5rem' }}
        >
          Logout
        </button>
      </div>
    );
  }

  return (
    <div className="navbar__item">
      <a href="/login" className="button button--sm button--primary">
        Login
      </a>
    </div>
  );
}
