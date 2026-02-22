import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { register } from '../lib/auth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Bot, Phone, BarChart3, ArrowRight } from 'lucide-react';

const features = [
  { icon: Bot, label: 'AI Voice Agents', desc: 'Build conversational voice AI that handles real phone calls' },
  { icon: Phone, label: 'Real Phone Calls', desc: 'Inbound & outbound via Twilio, SIP, or web browser' },
  { icon: BarChart3, label: 'Full Analytics', desc: 'Track performance, costs, transcripts, and conversions' },
];

export function RegisterPage() {
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [orgName, setOrgName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await register(email, password, name, orgName);
      navigate('/');
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Registration failed';
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex">
      {/* Left panel */}
      <div className="hidden lg:flex lg:w-[55%] relative flex-col justify-between p-12 overflow-hidden bg-sidebar">
        <div className="absolute inset-0 gradient-mesh" />
        <div className="absolute inset-0 noise-overlay" />
        <div className="absolute inset-0 dot-grid opacity-30" />
        <div className="absolute bottom-1/4 left-1/4 w-[400px] h-[400px] rounded-full bg-primary/5 blur-[120px]" />

        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-20">
            <div className="w-10 h-10 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" className="text-primary">
                <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" fill="currentColor" />
              </svg>
            </div>
            <div>
              <h1 className="text-xl font-display font-bold text-foreground leading-none">LOAD</h1>
              <p className="text-[10px] text-muted-foreground mt-0.5 tracking-wide uppercase">Voice AI Platform</p>
            </div>
          </div>

          <h2 className="text-4xl font-display font-bold text-foreground mb-5 leading-tight tracking-tight">
            Get started in<br />
            <span className="text-primary">under 5 minutes.</span>
          </h2>
          <p className="text-muted-foreground text-lg max-w-md leading-relaxed">
            Create your account, build an assistant, and make your first AI voice call — all from the dashboard.
          </p>

          <div className="mt-14 space-y-5">
            {features.map((f, i) => {
              const Icon = f.icon;
              return (
                <div
                  key={f.label}
                  className="flex items-start gap-4 animate-slide-up"
                  style={{ animationDelay: `${i * 100}ms`, animationFillMode: 'both' }}
                >
                  <div className="w-10 h-10 rounded-xl bg-primary/5 border border-primary/10 flex items-center justify-center shrink-0 mt-0.5">
                    <Icon size={18} className="text-primary/80" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-foreground">{f.label}</p>
                    <p className="text-sm text-muted-foreground mt-0.5">{f.desc}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <p className="text-xs text-muted-foreground/50 relative z-10">
          LOAD &mdash; Voice AI Platform &copy; {new Date().getFullYear()}
        </p>
      </div>

      {/* Right panel */}
      <div className="flex-1 flex items-center justify-center p-6 bg-background relative">
        <div className="absolute inset-0 noise-overlay" />

        <div className="max-w-[380px] w-full relative z-10 animate-slide-up">
          <div className="lg:hidden flex items-center justify-center gap-2.5 mb-10">
            <div className="w-9 h-9 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" className="text-primary">
                <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" fill="currentColor" />
              </svg>
            </div>
            <span className="text-lg font-display font-bold">LOAD</span>
          </div>

          <div className="text-center mb-8">
            <h2 className="text-2xl font-display font-bold tracking-tight">Create your account</h2>
            <p className="text-sm text-muted-foreground mt-2">Start building voice AI agents today</p>
          </div>

          {error && (
            <div className="bg-destructive/10 border border-destructive/20 text-destructive text-sm p-3.5 rounded-lg mb-5 flex items-start gap-2">
              <div className="w-1 h-1 rounded-full bg-destructive mt-1.5 shrink-0" />
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label htmlFor="name" className="text-xs font-medium">Full name</Label>
                <Input
                  id="name"
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  placeholder="Your name"
                  autoComplete="name"
                  className="h-11 bg-card border-border/60 focus:border-primary/40"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="org" className="text-xs font-medium">Organization</Label>
                <Input
                  id="org"
                  type="text"
                  value={orgName}
                  onChange={(e) => setOrgName(e.target.value)}
                  required
                  placeholder="Company name"
                  autoComplete="organization"
                  className="h-11 bg-card border-border/60 focus:border-primary/40"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="email" className="text-xs font-medium">Email</Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="you@company.com"
                autoComplete="email"
                className="h-11 bg-card border-border/60 focus:border-primary/40"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password" className="text-xs font-medium">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
                placeholder="Min 8 characters"
                autoComplete="new-password"
                className="h-11 bg-card border-border/60 focus:border-primary/40"
              />
            </div>
            <Button type="submit" disabled={loading} className="w-full h-11 font-semibold mt-2" size="lg">
              {loading ? (
                <span className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
                  Creating account
                </span>
              ) : (
                <span className="flex items-center gap-2">
                  Create account
                  <ArrowRight size={16} />
                </span>
              )}
            </Button>
          </form>

          <p className="text-center text-sm text-muted-foreground mt-8">
            Already have an account?{' '}
            <Link to="/login" className="text-primary font-medium hover:underline underline-offset-4">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
