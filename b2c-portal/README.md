# B2C Portal

A modern React application built with Vite, TypeScript, and Tailwind CSS.

## Features

- **Modern UI**: Built with React 18, TypeScript, and Tailwind CSS
- **Component Library**: Uses shadcn/ui components for consistent design
- **Routing**: React Router for navigation
- **State Management**: TanStack Query for server state
- **Authentication**: Supabase integration
- **Testing**: Vitest and Testing Library
- **E2E Testing**: Playwright for end-to-end testing

## Voice Agent Interface

The `/voice-agent` route features a VAPI-like assistant creation interface with:

### Key Features
- **Dark Theme**: Modern dark interface matching VAPI's design
- **Sidebar Navigation**: Left sidebar with BUILD and OBSERVE sections
- **Assistant Management**: List of assistants with creation capabilities
- **Configuration Tabs**: Model, Voice, Transcriber, Tools, Analysis, Advanced, and Widget tabs
- **Real-time Metrics**: Cost and latency visualization
- **Voice Configuration**: STT/TTS provider selection and voice options
- **Interactive Elements**: Buttons for testing, chatting, and calling assistants

### Interface Components
- **Left Sidebar**: Navigation with VAPI branding, user info, and menu items
- **Top Header**: Assistant name, ID, and action buttons (Code, Test, Chat, Talk)
- **Assistant Panel**: List of assistants with search and creation functionality
- **Configuration Area**: Tabbed interface for assistant configuration
- **Metrics Display**: Cost and latency breakdown with visual indicators

### Technical Implementation
- Uses Lucide React icons for consistent iconography
- Responsive design with Tailwind CSS
- State management for assistant configuration
- Integration with voice engine backend APIs
- Real-time audio processing capabilities

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

The application will be available at `http://localhost:5173`

### Testing

```bash
# Unit tests
npm test

# E2E tests
npm run test:e2e

# Test coverage
npm run test -- --coverage
```

### Building

```bash
npm run build
```

## Project Structure

```
src/
├── components/     # Reusable UI components
├── pages/         # Page components
├── hooks/         # Custom React hooks
├── lib/           # Utility functions and configurations
├── integrations/  # Third-party integrations
└── assets/        # Static assets
```

## Technologies Used

- **Frontend**: React 18, TypeScript, Vite
- **Styling**: Tailwind CSS, shadcn/ui
- **Routing**: React Router
- **State Management**: TanStack Query
- **Authentication**: Supabase
- **Testing**: Vitest, Testing Library, Playwright
- **Icons**: Lucide React
- **Forms**: React Hook Form with Zod validation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License.

