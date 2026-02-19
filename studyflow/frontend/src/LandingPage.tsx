import { Brain, MessageSquare, TrendingUp, Sparkles } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

function App() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-cyan-50">
      {/* Navigation Bar */}
      <nav className="container mx-auto px-4 py-4 flex justify-between items-center">
        <div className="flex items-center gap-2">
          <Brain className="w-8 h-8 text-blue-600" />
          <span className="text-xl font-bold text-gray-900">StudyFlow</span>
        </div>
        <button
          onClick={() => navigate('/login')}
          className="px-6 py-2 text-blue-600 hover:text-blue-700 font-medium transition-colors"
        >
          Sign In
        </button>
      </nav>

      {/* Hero Section */}
      <header className="container mx-auto px-4 py-16">
        <div className="text-center">
          <div className="inline-flex items-center gap-2 bg-blue-100 text-blue-700 px-4 py-2 rounded-full text-sm font-medium mb-6">
            <Sparkles className="w-4 h-4" />
            <span>AI-Powered Personal Tutoring</span>
          </div>
          <h1 className="text-6xl font-bold text-gray-900 mb-6">
            StudyFlow
          </h1>
          <p className="text-2xl text-gray-600 mb-4">
            Your personal tutor that listens, explains, and helps you learn smarter
          </p>
          <p className="text-lg text-gray-500 max-w-2xl mx-auto mb-8">
            Upload your school materials and get instant, intelligent tutoring.
            Ask questions, take practice exercises, and track your progress.
          </p>
          <button
            onClick={() => navigate('/login')}
            className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 rounded-lg text-lg font-semibold transition-colors shadow-lg"
          >
            Start Learning Free
          </button>
        </div>
      </header>

      {/* Features Section */}
      <section className="container mx-auto px-4 py-16">
        <h2 className="text-3xl font-bold text-center mb-12">How StudyFlow Helps You</h2>
        <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          <div className="bg-white p-8 rounded-xl shadow-md">
            <div className="bg-blue-100 w-12 h-12 rounded-lg flex items-center justify-center mb-4">
              <Brain className="w-6 h-6 text-blue-600" />
            </div>
            <h3 className="text-xl font-semibold mb-3">RAG-Powered Q&A</h3>
            <p className="text-gray-600">
              Ask questions from your study materials. Get accurate answers with references and explanations.
            </p>
          </div>

          <div className="bg-white p-8 rounded-xl shadow-md">
            <div className="bg-blue-100 w-12 h-12 rounded-lg flex items-center justify-center mb-4">
              <MessageSquare className="w-6 h-6 text-blue-600" />
            </div>
            <h3 className="text-xl font-semibold mb-3">Voice & Text Tutoring</h3>
            <p className="text-gray-600">
              Interact with Tutor Ama via voice or text. Get adaptive explanations at your level.
            </p>
          </div>

          <div className="bg-white p-8 rounded-xl shadow-md">
            <div className="bg-blue-100 w-12 h-12 rounded-lg flex items-center justify-center mb-4">
              <TrendingUp className="w-6 h-6 text-blue-600" />
            </div>
            <h3 className="text-xl font-semibold mb-3">Progress Tracking</h3>
            <p className="text-gray-600">
              Weekly reports for parents. Track exercises, scores, time spent, and strengths/weaknesses.
            </p>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12">Simple Pricing</h2>
          <div className="grid md:grid-cols-3 gap-6">
            <div className="bg-white p-6 rounded-lg shadow-md border-t-4 border-blue-600">
              <h3 className="font-bold text-xl mb-2">Free Trial</h3>
              <p className="text-gray-600 mb-4">30 minutes of tutoring</p>
              <p className="text-3xl font-bold mb-4">Free</p>
              <ul className="space-y-2 text-sm text-gray-600">
                <li>✓ Try all features</li>
                <li>✓ Upload 1 study material</li>
                <li>✓ No credit card required</li>
              </ul>
            </div>

            <div className="bg-white p-6 rounded-lg shadow-md border-t-4 border-blue-600 relative">
              <div className="absolute -top-3 right-4 bg-blue-600 text-white text-xs px-3 py-1 rounded-full">
                Most Popular
              </div>
              <h3 className="font-bold text-xl mb-2">Pay As You Learn</h3>
              <p className="text-gray-600 mb-4">₵20 = 100 minutes</p>
              <p className="text-3xl font-bold mb-4">₵20</p>
              <ul className="space-y-2 text-sm text-gray-600">
                <li>✓ No monthly commitment</li>
                <li>✓ Top-up anytime</li>
                <li>✓ Roll over unused minutes</li>
              </ul>
            </div>

            <div className="bg-white p-6 rounded-lg shadow-md border-t-4 border-blue-600">
              <h3 className="font-bold text-xl mb-2">Monthly Plan</h3>
              <p className="text-gray-600 mb-4">Unlimited tutoring</p>
              <p className="text-3xl font-bold mb-4">₵50</p>
              <ul className="space-y-2 text-sm text-gray-600">
                <li>✓ Unlimited questions</li>
                <li>✓ Unlimited exercises</li>
                <li>✓ Priority support</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="container mx-auto px-4 py-8 text-center text-gray-600">
        <p>&copy; 2025 StudyFlow by KasaAI. All rights reserved.</p>
      </footer>
    </div>
  )
}

export default App
