# DiaServe - Diaspora Real Estate Management Platform

## Project Overview

DiaServe (Diaserve Properties) is a full-stack real estate management platform connecting Ghanaians abroad with property investments in Ghana. It features property browsing, booking, payments, organization management, and a chat widget.

## Tech Stack

- **Backend**: Python 3 + FastAPI + MongoDB (Motor) + Pydantic v2
- **Frontend**: React + TypeScript + Vite + Tailwind CSS + shadcn/ui
- **Auth**: JWT (python-jose) + bcrypt
- **Package Manager**: bun (frontend), pip (backend)
- **API**: RESTful, async throughout

## Project Structure

```
backend/
  app/
    api/          # Route handlers
    core/         # Auth, database, scheduler
    models/       # Pydantic/MongoDB models
    services/     # Business logic
    config.py     # Settings (pydantic-settings)
    main.py       # FastAPI app entry
  tests/          # pytest tests
frontend/
  src/
    components/   # Reusable UI components (shadcn/ui)
    contexts/     # React context providers
    hooks/        # Custom React hooks
    lib/          # Utilities
    pages/        # Page components
```

## Critical Rules

### Code Style
- Backend: Follow PEP 8, use type hints, async/await for all IO
- Frontend: TypeScript strict mode, functional components only
- No hardcoded secrets - use environment variables
- No console.log in production code

### Testing
- Backend: pytest + pytest-asyncio for async tests
- Frontend: Vitest for unit tests
- Run backend tests: `cd backend && pytest`
- Run frontend build: `cd frontend && bun run build`

### Git Workflow
- Conventional commits: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`
- Never commit `.env` files or secrets

### API Patterns
- All backend routes under `/api/`
- Use Pydantic models for request/response validation
- Return consistent JSON response format
- Handle errors with FastAPI HTTPException

## Environment Variables

```bash
# Backend (.env)
MONGODB_URL=           # MongoDB connection string
SECRET_KEY=            # JWT secret
ADMIN_EMAIL=           # Default admin email
ADMIN_PASSWORD=        # Default admin password

# Frontend (.env)
VITE_API_URL=          # Backend API URL
```

## Available Commands

- `/plan` - Create implementation plan
- `/tdd` - Test-driven development workflow
- `/code-review` - Review code quality
- `/build-fix` - Fix build errors
- `/verify` - Verify implementation
- `/test-coverage` - Check test coverage
- `/python-review` - Python-specific code review
- `/refactor-clean` - Clean refactoring
