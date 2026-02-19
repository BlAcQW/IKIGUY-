import React from 'react';
import Layout from '@theme/Layout';
import BrowserOnly from '@docusaurus/BrowserOnly';
import SignupForm from '../components/Auth/SignupForm';

export default function Signup() {
  return (
    <Layout title="Sign Up" description="Create a KasaAI Documentation account">
      <BrowserOnly fallback={<div>Loading...</div>}>
        {() => <SignupForm />}
      </BrowserOnly>
    </Layout>
  );
}
