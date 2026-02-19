# DevotionalFlow - Project Planning & Architecture

## 🔄 Build & Deployment Rules

### Frontend Rebuild & Service Restart
**CRITICAL**: Always rebuild the frontend and restart services when making changes.

#### Quick Rebuild (Recommended)
Use the rebuild script for convenience:
```bash
cd /opt/kasaai/apps/devotionalflow
./rebuild.sh          # Rebuild frontend + restart backend + reload nginx
./rebuild.sh frontend # Rebuild frontend only
./rebuild.sh backend  # Restart backend only
```

#### Manual Rebuild Steps

1. **After Frontend Changes**:
   ```bash
   cd /opt/kasaai/apps/devotionalflow/frontend
   npm run build
   sudo systemctl reload nginx
   ```

2. **After Backend Changes**:
   ```bash
   sudo systemctl restart kasaai-devotionalflow-backend
   ```

3. **After Configuration Changes**:
   - Frontend config: Rebuild frontend + reload nginx
   - Backend config: Restart backend service
   - Both: Rebuild frontend + restart backend + reload nginx

4. **Verification**:
   - Check service status: `systemctl status kasaai-devotionalflow-backend`
   - Check nginx status: `systemctl status nginx`
   - Verify build output exists: `ls -la frontend/dist/`

#### Agent Rules
- **ALWAYS** rebuild frontend after making frontend changes (React/TypeScript files)
- **ALWAYS** restart backend after making backend changes (Python files)
- **ALWAYS** verify services are running after restart
- **NEVER** skip rebuild/restart - changes won't be reflected without it
- **ALWAYS** check build output and service status after deployment

**Rule**: Never commit frontend or backend changes without rebuilding/restarting to ensure changes are reflected in production.

---

## 📐 Architecture Overview

### Tech Stack
- **Frontend**: React + TypeScript + Vite + Tailwind CSS
- **Backend**: FastAPI + Python + MongoDB
- **Authentication**: Supabase
- **Deployment**: Nginx (frontend) + Systemd (backend)

### Project Structure
```
apps/devotionalflow/
├── frontend/          # React frontend application
├── backend/           # FastAPI backend application
└── README.md          # Project documentation
```

---

## 🎨 Design Principles

- **Mobile-First**: All designs prioritize mobile experience
- **Spiritual Aesthetic**: Navy, gold, teal color palette
- **Modern UI**: Clean, minimal, with subtle gradients and shadows
- **Accessibility**: WCAG 2.1 AA compliance

---

## 🧱 Code Structure & Modularity

- **File Length**: Never create files longer than 500 lines
- **Module Organization**: Group by feature/responsibility
- **Imports**: Prefer relative imports within packages

---

## 🧪 Testing & Reliability

- **Unit Tests**: Always create Pytest tests for new features
- **Test Location**: `/tests` folder mirroring app structure
- **Test Coverage**: At least 1 expected use, 1 edge case, 1 failure case

---

## ✅ Task Completion

- **Mark Tasks**: Update `TASK.md` immediately after completion
- **Add Discovered Tasks**: Add to "Discovered During Work" section
- **Honest Status**: Always be honest about completion state

---

## 📎 Style & Conventions

- **Language**: Python (backend), TypeScript (frontend)
- **Formatting**: `black` for Python, Prettier for TypeScript
- **Type Hints**: Always use type hints in Python
- **Validation**: Use `pydantic` for data validation
- **API Framework**: FastAPI
- **Database**: MongoDB
- **Auth**: Supabase

---

## 📚 Documentation

- **Update README**: When features change or dependencies update
- **Code Comments**: Comment non-obvious code
- **Inline Comments**: Use `# Reason:` for complex logic explanations

---

## 🧠 AI Behavior Rules

- **Never assume**: Ask questions if uncertain
- **Never hallucinate**: Only use verified packages
- **Confirm paths**: Verify file paths exist before referencing
- **Never delete**: Don't delete code unless explicitly instructed

---

## Versioning

- **Git Commits**: Create commit after each new task completion
- **Commit Messages**: Use clear, descriptive messages

