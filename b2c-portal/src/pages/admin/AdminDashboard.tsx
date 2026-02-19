import React from 'react';
import { Navigate } from 'react-router-dom';

export default function AdminDashboard() {
  // Redirect to Users page by default
  return <Navigate to="/admin/users" replace />;
}