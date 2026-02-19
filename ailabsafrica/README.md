# AI Labs Africa - KasaAI Platform

[![React](https://img.shields.io/badge/React-18.3.1-blue.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.5.3-blue.svg)](https://www.typescriptlang.org/)
[![Vite](https://img.shields.io/badge/Vite-5.4.1-purple.svg)](https://vitejs.dev/)
[![Supabase](https://img.shields.io/badge/Supabase-2.54.0-green.svg)](https://supabase.com/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4.11-38B2AC.svg)](https://tailwindcss.com/)

## 🌍 Overview

AI Labs Africa is a pioneering AI innovation platform focused on transforming businesses and communities across Africa. Our flagship product, **KasaAI**, is a next-generation AI-powered voice and chat automation platform designed to help businesses engage customers, drive sales, and streamline operations effortlessly.

### 🚀 Key Features

- **Multi-channel Support**: Voice calls, WhatsApp, SMS, and web chat
- **Natural Conversations**: Human-like AI interactions in multiple languages
- **24/7 Availability**: Round-the-clock customer engagement
- **Enterprise Security**: Secure and scalable solutions
- **Local Innovation**: Built by Africans, for Africa
- **AI-Powered Assistant Creation**: Intelligent website content extraction and system prompt generation
- **Template System**: Pre-built voice agent templates with customization options
- **Guest Mode**: Create assistants without full authentication
- **Advanced Analytics**: Comprehensive usage tracking and performance monitoring
- **Payment Integration**: Secure payment processing with multiple gateways
- **Real-time Monitoring**: Live usage tracking and billing management
- **Voice Agent Analytics**: Detailed call history, transcripts, and conversation summaries
- **Help System**: Comprehensive help section with tooltips and contextual guidance

### 🎯 Voice Agent Details & Analytics

The platform now includes comprehensive voice agent analytics and call management:

- **Call History**: View all calls with detailed information including start/end times, duration, cost, and status
- **Conversation Transcripts**: Access full conversation transcripts for each call
- **AI-Generated Summaries**: Automatic conversation summaries using Gemini AI
- **Analytics Dashboard**: Visual charts showing call volume, cost trends, and success rates
- **Status Distribution**: Pie charts showing call status and communication medium distribution
- **Filtering & Search**: Filter calls by time range and status
- **Export Capabilities**: Download call data and transcripts

### 🆘 Help System

A comprehensive help system has been integrated throughout the platform:

- **Contextual Tooltips**: Help icons (?) provide contextual guidance throughout the interface
- **Help Section**: Dedicated help page with pricing guides, FAQs, and feature documentation
- **Pricing Information**: Dynamic pricing display based on region and communication medium
- **Feature Guides**: Step-by-step guides for platform features
- **Support Resources**: Links to documentation and support channels

## 🏗️ Architecture

### Frontend Stack

- **React 18** with TypeScript for type-safe development
- **Vite** for fast development and building
- **React Router** for client-side routing
- **TanStack Query** for server state management
- **Radix UI** components with **shadcn/ui** design system
- **Tailwind CSS** for styling with custom African-inspired theme

### Backend & Infrastructure

- **Supabase** for backend-as-a-service
  - PostgreSQL database with comprehensive schema
  - Edge Functions for serverless API
  - Authentication and authorization with RBAC
  - Real-time subscriptions
  - Row Level Security (RLS) policies
- **Vapi** integration for voice AI capabilities
- **Gemini API** for intelligent content extraction and analysis

### Key Technologies

- **React Hook Form** with **Zod** validation
- **Lucide React** for icons
- **Recharts** for data visualization
- **Sonner** for toast notifications
- **Date-fns** for date manipulation
- **Vitest** for comprehensive testing
- **React Testing Library** for component testing

## 📁 Project Structure

```
ailabsafrica/
├── src/
│   ├── components/
│   │   ├── dashboard/          # Dashboard-specific components
│   │   ├── ui/                 # Reusable UI components (shadcn/ui)
│   │   ├── Navigation.tsx      # Main navigation component
│   │   ├── VoiceAgentTemplates.tsx  # Template selection interface
│   │   ├── TemplateCustomization.tsx # Template management
│   │   ├── TemplateConfiguration.tsx # Integration configuration
│   │   ├── help/               # Help system components
│   │   │   ├── HelpSection.tsx # Comprehensive help page
│   │   │   ├── HelpTooltip.tsx # Contextual help tooltips
│   │   │   └── HelpButton.tsx  # Reusable help button
│   │   └── debug/              # Debug components
│   ├── contexts/
│   │   ├── AuthContext.tsx     # Authentication context
│   │   └── HelpContext.tsx     # Help system context and navigation
│   ├── hooks/                  # Custom React hooks
│   ├── integrations/
│   │   └── supabase/           # Supabase client and types
│   ├── lib/
│   │   └── utils.ts            # Utility functions
│   ├── pages/
│   │   ├── demos/              # AI demo pages
│   │   ├── Auth.tsx            # Authentication page
│   │   ├── Dashboard.tsx       # User dashboard
│   │   ├── Demos.tsx           # Demo showcase
│   │   ├── Home.tsx            # Landing page
│   │   ├── CreateAssistant.tsx # Assistant creation wizard
│   │   ├── VoiceAgents.tsx     # Voice agent management
│   │   ├── VoiceAgentDetails.tsx # Detailed agent analytics and call history
│   │   ├── CustomDemos.tsx     # Custom demo management
│   │   ├── GuestDashboard.tsx  # Guest user interface
│   │   └── ...                 # Other pages
│   ├── tests/                  # Comprehensive test suite
│   └── main.tsx                # Application entry point
├── supabase/
│   ├── functions/              # Edge Functions
│   │   ├── create-assistant/   # AI assistant creation
│   │   ├── extract-site-info/  # Website content extraction
│   │   ├── generate-demo-html/ # HTML demo generation
│   │   ├── manage-assistant/   # Assistant management
│   │   ├── manage-custom-demos/ # Demo management
│   │   ├── manage-custom-templates/ # Template management
│   │   ├── guest-assistant-management/ # Guest user operations
│   │   ├── list-vapi-voices/   # Voice listing
│   │   ├── list-custom-demos/  # Demo listing
│   │   ├── process-payment/    # Payment processing
│   │   ├── verify-payment/     # Payment verification
│   │   └── ...                 # Other functions
│   └── migrations/             # Database migrations
├── public/                     # Static assets
└── package.json                # Dependencies and scripts
```

## 🎨 Design System

The project uses a custom design system with African-inspired colors:

- **Tech Blue**: Primary brand color
- **African Gold**: Accent color for highlights and CTAs
- **Custom Theme**: Tailwind CSS with shadcn/ui components

## 🚀 Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- Supabase account and project
- Docker Desktop (for local Supabase development)

### Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd ailabsafrica
   ```

2. **Install dependencies**

   ```bash
   npm install
   ```

3. **Environment Setup**
   Create a `.env` file in the root directory:

   ```env
   VITE_SUPABASE_URL=your_supabase_url
   VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
   VITE_VAPI_PUBLIC_KEY=your_vapi_public_key
   VITE_GEMINI_API_KEY=your_gemini_api_key
   ```

4. **Start development server**

   ```bash
   npm run dev
   ```

5. **Open your browser**
   Navigate to `http://localhost:8080`

### Building for Production

```bash
npm run build
```

## 🎯 Features & Pages

### 🏠 Home Page

- Hero section with African-inspired design
- KasaAI product showcase
- Industry solutions overview
- Call-to-action sections
- Interactive demo showcase

### 🤖 AI Assistant Creation

**Comprehensive assistant creation wizard with intelligent features:**

- **Website Content Extraction**: Automatically extract relevant information from business websites using Gemini AI
- **System Prompt Generation**: AI-powered system prompt creation based on extracted content and user input
- **Voice Selection**: Choose from VAPI's extensive voice library
- **Template System**: Pre-built templates for common use cases (Appointment Scheduler, Customer Support, etc.)
- **Template Customization**: Modify existing templates and save custom versions
- **Integration Configuration**: Set up calendar, email, WhatsApp, Google Sheets, CRM, and database integrations
- **Guest Mode**: Create assistants without full authentication using email/password
- **Real-time Preview**: Preview generated HTML demos before deployment
- **SFTP Upload**: Automatic deployment to web server with email notifications

### 📊 Dashboard

- **User Wallet Management**: Load money and purchase usage bundles
- **Usage Analytics**: Real-time usage tracking with time-based filtering
- **Demo Booking History**: Track demo interactions and conversions
- **Transaction Tracking**: Complete payment and billing history
- **Voice Agent Management**: Create, edit, pause, resume, and delete assistants
- **Account Settings**: Profile management and security settings
- **Advanced Analytics**: Comprehensive usage, performance, and conversion tracking

### 🔐 Authentication & Security

- **Supabase Auth Integration**: Secure user registration and login
- **Role-Based Access Control**: Admin, user, demo, and guest roles
- **Two-Factor Authentication**: Enhanced security with TOTP
- **Email Verification**: Secure email verification process
- **Password Reset**: Secure password reset functionality
- **Session Management**: Automatic session timeout and refresh
- **Guest Access**: Password-based access for non-authenticated users

### 🛡️ Security Enhancements

**Comprehensive security framework with advanced protection:**

- **Rate Limiting**: API endpoint protection with configurable limits
- **Input Validation**: Zod schema validation for all user inputs
- **SQL Injection Protection**: Parameterized queries and input sanitization
- **XSS Protection**: HTML encoding and Content Security Policy (CSP)
- **CSRF Protection**: Cross-Site Request Forgery prevention
- **Password Security**: Secure hashing, strength validation, and generation
- **Session Security**: Secure session management with timeout and refresh
- **API Security**: Request validation, authentication, and authorization
- **Security Headers**: Comprehensive security headers implementation
- **Vulnerability Scanning**: Automated security scanning with SecurityScanner component
- **Input Sanitization**: String, HTML, SQL, and filename sanitization
- **Security Monitoring**: Real-time security monitoring and alerting

### 💳 Payment System

- **Payment Gateway Integration**: Support for Flutterwave, Paystack, and other gateways
- **Usage-Based Billing**: Pay-per-minute usage tracking
- **Bundle Purchases**: Pre-purchase usage bundles at discounted rates
- **Invoice Generation**: Professional invoice creation and management
- **Refund System**: Full and partial refund processing
- **Payment Analytics**: Comprehensive payment tracking and reporting
- **Multi-currency Support**: Support for multiple currencies

### 🎨 Template System

**Comprehensive template management with advanced features:**

- **Pre-built Templates**: Industry-specific templates for common use cases
- **Template Categories**: Beginner, Intermediate, and Advanced difficulty levels
- **Template Customization**: Modify and save custom template versions
- **Template Management**: Create, edit, delete, and duplicate templates
- **Template Versioning**: Version control for template updates
- **Template Search**: Advanced search and filtering functionality
- **Integration Configuration**: Set up comprehensive integrations for each template
- **Template Analytics**: Track usage, success rates, and popularity

### 🌙 Theme System

**Advanced theming with user preference support:**

- **Dark Mode**: Complete dark theme with smooth transitions
- **Light Mode**: Clean light theme optimized for readability
- **System Preference**: Automatic theme switching based on OS preference
- **Theme Persistence**: User theme preference saved across sessions
- **Accessibility**: High contrast themes and proper color ratios
- **Custom Branding**: AI Labs Africa themed gradients and colors
- **Theme Toggle**: Easy switching between themes via navigation

### ♿ Accessibility Features

**Comprehensive accessibility support for all users:**

- **Screen Reader Support**: Comprehensive ARIA labels and semantic HTML structure
- **Keyboard Navigation**: Full keyboard accessibility with proper focus management
- **Global Shortcuts**: Alt+1-4 for navigation, Alt+H for keyboard shortcuts help
- **Focus Traps**: Proper focus management for modals, dialogs, and dropdowns
- **Live Regions**: Screen reader announcements for important actions and state changes
- **High Contrast**: Enhanced visibility and color contrast for users with visual impairments
- **Semantic Structure**: Proper heading hierarchy, landmark roles, and navigation structure
- **Alternative Text**: Descriptive alt text for all images, icons, and interactive elements
- **Form Accessibility**: Proper labels, error announcements, and validation feedback
- **Mobile Accessibility**: Touch-friendly targets and gesture support

### 📈 Analytics & Reporting

**Advanced analytics with comprehensive tracking:**

- **Usage Analytics**: User behavior tracking and feature usage analysis
- **Performance Metrics**: System performance monitoring and API statistics
- **Conversion Tracking**: Demo-to-customer conversion funnel analysis
- **Real-time Analytics**: Live metrics and performance updates
- **Custom Reports**: Generate and export custom reports in multiple formats
- **Export Functionality**: CSV export for all analytics data
- **Time Range Filtering**: 7d, 30d, 90d, 1y time range selection
- **Chart Visualizations**: Line charts, area charts, bar charts, and pie charts

### 🎭 Demo System

**Comprehensive demo management with advanced features:**

- **Demo Analytics**: Track demo usage, engagement metrics, and conversion rates
- **Demo Sharing**: Social sharing to Twitter, Facebook, LinkedIn, WhatsApp, and Email
- **Demo Embedding**: Create embed codes for external websites with customization
- **Demo Versioning**: Version control for demo updates with rollback functionality
- **Demo Comments**: Feedback system with ratings and moderation
- **Demo Preview**: Real-time preview with HTML copying and sharing
- **QR Code Generation**: Easy mobile sharing with QR codes
- **Standalone Pages**: Full standalone demo pages with custom branding

### 🤖 Voice Agent Management

**Complete voice agent lifecycle management:**

- **Assistant Creation**: Intelligent assistant creation with AI-powered prompts
- **Assistant Cloning**: Clone existing assistants with customization options
- **Bulk Operations**: Bulk delete, pause, and resume functionality
- **Assistant Analytics**: Call analytics, usage patterns, and performance metrics
- **Status Management**: Pause/resume functionality with visual indicators
- **Assistant Deletion**: Secure deletion with VAPI integration
- **Voice Selection**: Extensive voice library from VAPI
- **Real-time Updates**: Live status updates across the application

### 🧪 Testing & Quality Assurance

**Comprehensive testing infrastructure:**

- **Unit Tests**: 465+ passing tests with comprehensive coverage (55% improvement)
- **Integration Tests**: API endpoint testing with proper setup and teardown
- **Component Testing**: React Testing Library for component behavior with enhanced Radix UI support
- **Error Handling**: Comprehensive error handling and edge case testing
- **Performance Testing**: Response time and concurrent request testing
- **Accessibility Testing**: Screen reader compatibility and keyboard navigation
- **Test Utilities**: Enhanced helper functions and mock setup for efficient testing
- **E2E Testing**: ✅ **IMPLEMENTED** - Playwright for end-to-end testing with database verification
- **Recent Improvements**:
  - Fixed TemplateConfiguration tests and resolved act() warnings
  - Implemented comprehensive CreateAssistant Phase 1.5 testing
  - Added E2E testing infrastructure with Playwright
  - Enhanced template system with preview, testing, and analytics features
  - Added voice selection, assistant type selection, and VAPI integration tests
  - Enhanced form validation and integration testing coverage
  - Implemented comprehensive security enhancements with rate limiting, input validation, and vulnerability scanning
  - Added dark mode theme system with light/dark/system theme switching

### 🔧 Performance Optimization

**Advanced performance optimization features:**

- **Code Splitting**: React.lazy() and Suspense for reduced bundle size
- **Caching Strategy**: Enhanced Vite configuration with manual chunk splitting
- **Service Worker**: Offline functionality, API caching, and background sync
- **PWA Support**: Progressive Web App with native-like experience
- **Image Optimization**: Lazy loading, WebP support, and responsive images
- **Bundle Analysis**: Identify optimization opportunities and large dependencies
- **Performance Monitoring**: Real-time performance tracking with alerts
- **Memory Management**: Proper cleanup and resource management

## 🛠️ Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run build:dev` - Build for development
- `npm run lint` - Run ESLint
- `npm run preview` - Preview production build
- `npm test` - Run test suite
- `npm run test:ui` - Run tests with UI
- `npm run test:coverage` - Generate test coverage report

### Code Style

- **TypeScript** for type safety
- **ESLint** for code linting
- **Prettier** for code formatting
- **PEP8** equivalent practices for React/TypeScript

### Component Guidelines

- Use functional components with hooks
- Implement proper TypeScript interfaces
- Follow shadcn/ui component patterns
- Use Tailwind CSS for styling
- Implement responsive design
- Add comprehensive unit tests
- Include proper error handling

## 🌐 Deployment

### Supabase Setup

1. Create a new Supabase project
2. Run database migrations:
   ```bash
   supabase db push
   ```
3. Deploy Edge Functions:
   ```bash
   supabase functions deploy
   ```
4. Set up environment variables in Supabase dashboard

### Environment Variables

Ensure all required environment variables are set in your deployment platform:

- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`
- `VITE_VAPI_PUBLIC_KEY`
- `VITE_GEMINI_API_KEY`

### Production Deployment

The application is configured for production deployment with:

- **GitHub Actions**: Automated CI/CD pipeline
- **Docker Support**: Containerized deployment
- **CDN Integration**: Static asset optimization
- **SSL/HTTPS**: Secure connections
- **Performance Monitoring**: Real-time monitoring and alerting

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Write meaningful commit messages
- Add TypeScript types for all new features
- Include proper error handling
- Test your changes thoroughly
- Update documentation as needed
- Follow the established code style
- Add unit tests for new functionality

## 📱 Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## 🔒 Security

- JWT-based authentication via Supabase
- Secure API endpoints with proper authorization
- Input validation and sanitization
- HTTPS enforcement in production
- Row Level Security (RLS) policies
- Two-factor authentication support
- Session management with automatic timeout
- Rate limiting and DDoS protection

## 📄 License

This project is proprietary software developed by AI Labs Africa.

## 📞 Support

For support and inquiries:

- Email: [contact@ailabsafrica.com]
- Website: [https://ailabsafrica.com]
- Documentation: [https://docs.ailabsafrica.com]

---

**Built with ❤️ in Africa, for Africa**
