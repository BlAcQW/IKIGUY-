import React from 'react';
import { AuthProvider } from '../components/Auth/AuthContext';

// Default implementation, that you can customize
export default function Root({ children }) {
  return (
    <AuthProvider>
      {children}
    </AuthProvider>
  );
}
