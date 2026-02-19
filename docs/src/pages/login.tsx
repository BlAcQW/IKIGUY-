import React from 'react';
import Layout from '@theme/Layout';
import BrowserOnly from '@docusaurus/BrowserOnly';
import LoginForm from '../components/Auth/LoginForm';

export default function Login() {
  return (
    <Layout title="Login" description="Login to KasaAI Documentation">
      <BrowserOnly fallback={<div>Loading...</div>}>
        {() => <LoginForm />}
      </BrowserOnly>
    </Layout>
  );
}
