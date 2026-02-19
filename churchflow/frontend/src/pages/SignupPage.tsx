/**
 * Church Signup Page - ChurchFlow SaaS
 *
 * Public signup page for new churches to register.
 */

import { useNavigate } from 'react-router-dom';
import { SignupWizard } from '../components/onboarding';

export default function SignupPage() {
  const navigate = useNavigate();
  const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:30030';

  const handleComplete = (organizationId: string) => {
    // Store organization ID and redirect to login
    localStorage.setItem('signup_organization_id', organizationId);

    // Show success message
    alert('Church registration complete! Please log in to get started.');

    // Redirect to login
    navigate('/login');
  };

  const handleError = (message: string) => {
    console.error('Signup error:', message);
    // Error is displayed in the wizard component
  };

  return (
    <SignupWizard
      apiBaseUrl={apiBaseUrl}
      onComplete={handleComplete}
      onError={handleError}
    />
  );
}
