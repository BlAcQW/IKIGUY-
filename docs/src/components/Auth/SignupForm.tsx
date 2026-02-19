import React, { useState } from 'react';
import { useAuth } from './AuthContext';
import styles from './Auth.module.css';

export default function SignupForm() {
  const { signup } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    if (password.length < 8) {
      setError('Password must be at least 8 characters');
      setLoading(false);
      return;
    }

    try {
      await signup(email, password, fullName);

      // Check for redirect parameter in URL
      const urlParams = new URLSearchParams(window.location.search);
      const redirectTo = urlParams.get('redirect');

      // Redirect to intended page or home
      window.location.href = redirectTo && redirectTo.startsWith('/') ? redirectTo : '/';
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Signup failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.authContainer}>
      <div className={styles.authCard}>
        <h1 className={styles.authTitle}>Create Your Account</h1>
        <p className={styles.authSubtitle}>
          Get access to KasaAI documentation and resources
        </p>

        {error && (
          <div className={styles.errorMessage}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className={styles.authForm}>
          <div className={styles.formGroup}>
            <label htmlFor="fullName" className={styles.label}>
              Full Name (Optional)
            </label>
            <input
              id="fullName"
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className={styles.input}
              placeholder="John Doe"
            />
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="email" className={styles.label}>
              Email Address
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className={styles.input}
              placeholder="your.email@example.com"
            />
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="password" className={styles.label}>
              Password (min. 8 characters)
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              className={styles.input}
              placeholder="••••••••"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className={styles.submitButton}
          >
            {loading ? 'Creating account...' : 'Sign Up'}
          </button>
        </form>

        <p className={styles.authFooter}>
          Already have an account?{' '}
          <a href="/login" className={styles.link}>
            Login
          </a>
        </p>
      </div>
    </div>
  );
}
