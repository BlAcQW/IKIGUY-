import React from 'react';
import { Link } from 'react-router-dom';
import { CheckSquare, Phone, Zap, Sparkles } from 'lucide-react';

// EventFlow Landing Page - AI-Powered Event Management
export const Landing: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-green-50">
      {/* Hero Section */}
      <header className="container mx-auto px-4 py-16">
        <div className="text-center">
          <div className="inline-flex items-center gap-2 bg-emerald-100 text-emerald-700 px-4 py-2 rounded-full text-sm font-medium mb-6">
            <Sparkles className="w-4 h-4" />
            <span>AI-Powered Event Management</span>
          </div>
          <h1 className="text-6xl font-bold text-gray-900 mb-6">
            EventFlow
          </h1>
          <p className="text-2xl text-gray-600 mb-4">
            Plan less. Celebrate more.
          </p>
          <p className="text-lg text-gray-500 max-w-2xl mx-auto mb-8">
            AI-driven event planning with automated voice calls, smart task management,
            and intelligent follow-ups. Let AI handle the coordination while you focus on the experience.
          </p>
          <Link to="/login">
            <button className="bg-emerald-600 hover:bg-emerald-700 text-white px-8 py-4 rounded-lg text-lg font-semibold transition-colors shadow-lg">
              Start Planning
            </button>
          </Link>
        </div>
      </header>

      {/* Features Section */}
      <section className="container mx-auto px-4 py-16">
        <h2 className="text-3xl font-bold text-center mb-12">Intelligent Automation</h2>
        <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          <div className="bg-white p-8 rounded-xl shadow-md">
            <div className="bg-emerald-100 w-12 h-12 rounded-lg flex items-center justify-center mb-4">
              <CheckSquare className="w-6 h-6 text-emerald-600" />
            </div>
            <h3 className="text-xl font-semibold mb-3">Smart Task Generation</h3>
            <p className="text-gray-600">
              AI creates comprehensive task lists based on your event type, budget, and guests.
            </p>
          </div>

          <div className="bg-white p-8 rounded-xl shadow-md">
            <div className="bg-emerald-100 w-12 h-12 rounded-lg flex items-center justify-center mb-4">
              <Phone className="w-6 h-6 text-emerald-600" />
            </div>
            <h3 className="text-xl font-semibold mb-3">Automated Voice Calls</h3>
            <p className="text-gray-600">
              Ama calls responsible persons, gets updates, and logs status automatically.
            </p>
          </div>

          <div className="bg-white p-8 rounded-xl shadow-md">
            <div className="bg-emerald-100 w-12 h-12 rounded-lg flex items-center justify-center mb-4">
              <Zap className="w-6 h-6 text-emerald-600" />
            </div>
            <h3 className="text-xl font-semibold mb-3">Smart Escalation</h3>
            <p className="text-gray-600">
              Overdue tasks trigger automatic reminders via SMS, WhatsApp, and voice calls.
            </p>
          </div>
        </div>
      </section>

      {/* Use Cases */}
      <section className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12">Perfect For</h2>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="bg-white p-6 rounded-lg shadow-md">
              <h3 className="font-semibold text-lg mb-2">🎉 Weddings</h3>
              <p className="text-gray-600">Coordinate vendors, track RSVPs, manage timelines effortlessly.</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow-md">
              <h3 className="font-semibold text-lg mb-2">🎤 Conferences</h3>
              <p className="text-gray-600">Manage speakers, logistics, catering with automated follow-ups.</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow-md">
              <h3 className="font-semibold text-lg mb-2">🎸 Concerts</h3>
              <p className="text-gray-600">Handle sound, security, ticketing with AI-powered coordination.</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow-md">
              <h3 className="font-semibold text-lg mb-2">🏢 Corporate Events</h3>
              <p className="text-gray-600">Streamline planning, reduce manual follow-ups, track everything.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section className="container mx-auto px-4 py-16">
        <div className="max-w-xl mx-auto bg-white p-8 rounded-xl shadow-lg">
          <h2 className="text-3xl font-bold text-center mb-6">Pay Per Use</h2>
          <div className="space-y-4 mb-6">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Event creation</span>
              <span className="font-semibold">Free</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Voice call (per minute)</span>
              <span className="font-semibold">₵2.00</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">SMS reminder</span>
              <span className="font-semibold">₵0.20</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">WhatsApp message</span>
              <span className="font-semibold">₵0.30</span>
            </div>
          </div>
          <Link to="/login">
            <button className="w-full bg-emerald-600 hover:bg-emerald-700 text-white py-3 rounded-lg font-semibold transition-colors">
              Start Free Event
            </button>
          </Link>
          <p className="text-center text-sm text-gray-500 mt-4">
            ₵50 credit on signup • Only pay for what you use
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer className="container mx-auto px-4 py-8 text-center text-gray-600">
        <p>&copy; 2025 EventFlow by KasaAI. All rights reserved. | v1.0</p>
      </footer>
    </div>
  );
};
