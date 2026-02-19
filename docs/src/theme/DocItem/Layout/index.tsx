import React from 'react';
import { useLocation } from '@docusaurus/router';
import Layout from '@theme-original/DocItem/Layout';
import type LayoutType from '@theme/DocItem/Layout';
import type { WrapperProps } from '@docusaurus/types';
import ProtectedRoute from '../../../components/Auth/ProtectedRoute';

type Props = WrapperProps<typeof LayoutType>;

export default function LayoutWrapper(props: Props): JSX.Element {
  const location = useLocation();

  // Check if current page is in internal documentation
  const isInternalDoc = location.pathname.startsWith('/internal');

  // If internal doc, wrap with ProtectedRoute requiring internal access
  if (isInternalDoc) {
    return (
      <ProtectedRoute requiredRole="internal">
        <Layout {...props} />
      </ProtectedRoute>
    );
  }

  // For public docs, render normally
  return <Layout {...props} />;
}
