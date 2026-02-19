# DevotionalFlow

> Holy Spirit Inspired Mobile-First Devotional Platform

[![Status](https://img.shields.io/badge/status-production--ready-green)](https://github.com)
[![Frontend](https://img.shields.io/badge/frontend-production--ready-green)](https://github.com)
[![Backend](https://img.shields.io/badge/backend-production--ready-green)](https://github.com)
[![License](https://img.shields.io/badge/license-MIT-blue)](https://github.com)

---

## 📖 Overview

**DevotionalFlow** is a mobile-first SaaS platform designed to empower pastors to publish daily devotionals effortlessly while building a deeply connected digital community around their ministry. It blends beautiful design, powerful writing tools, and Holy Spirit inspired spiritual engagement.

### Vision

To revolutionize how pastors share spiritual content and connect with their congregation in the digital age, making daily devotional publishing as simple and inspiring as the messages themselves.

### Target Users

- **Pastors** (Content Creators): Publish, schedule, and manage devotionals
- **Readers** (Congregation & Global Followers): Engage with daily spiritual content

### Key Differentiators

- 🎨 **Beautiful Spiritual Design**: Custom color palette (navy, gold, teal) with calming typography
- ✨ **Holy Spirit Inspired**: Enhanced features including text-to-speech, summaries, and scripture explanations
- 📱 **Mobile-First**: Optimized for on-the-go devotional reading and publishing
- 💬 **Social Engagement**: Comments, likes, shares, and community building
- ⏰ **Smart Scheduling**: Plan devotionals for weeks or months in advance
- 📊 **Analytics Dashboard**: Track engagement and understand your audience

---

## 🚨 Current Implementation Status

### ✅ Frontend & Backend: **Production Ready**

**Port:** 30042
**Domains:**
- Primary: freshmanna365.com (and www.freshmanna365.com)
- Secondary: freshmanna.ailabsafrica.com
**API:**
- Primary: api.freshmanna365.com
- Secondary: freshmanna-api.ailabsafrica.com

### ✅ Core Features (Working)

**Authentication & Users:**
- ✅ Supabase authentication (login/signup)
- ✅ Role-based access (admin, pastor, reader)
- ✅ User profiles with avatar upload
- ✅ Default users (admin@ailabsafrica.com)

**Devotional Management:**
- ✅ Create, edit, delete devotionals
- ✅ Rich content blocks (paragraph, scripture, prayer, reflection)
- ✅ Cover image upload (Hetzner Storage)
- ✅ **Pexels stock photo integration** (search 100,000+ free photos)
- ✅ **Preview devotionals before publishing**
- ✅ Schedule for future publication
- ✅ Draft/published status
- ✅ Categories and tags
- ✅ **Advanced Series Management** (Complete: Dec 2024)
  - ✅ Full CRUD operations for series
  - ✅ Auto-scheduling with daily intervals
  - ✅ **Drag-and-drop reordering with @dnd-kit**
  - ✅ **Interactive Series Editor Dialog**
  - ✅ Auto-renumbering when devotionals removed
  - ✅ Public series browse page with search
  - ✅ Series detail pages with devotional lists
  - ✅ Author dashboard for series management
  - ✅ Optimistic UI updates
  - ✅ Part numbers and sequencing
  - ✅ Bulk scheduling operations

**Scripture Integration:**
- ✅ Bible API integration (API.Bible)
- ✅ ESV API support
- ✅ Scripture lookup and autocomplete
- ✅ Multiple translations
- ✅ Formatted scripture blocks

**Social Features:**
- ✅ Comments system with replies
- ✅ Like devotionals and comments
- ✅ Bookmark devotionals
- ✅ Reading progress tracking
- ✅ Share functionality

**Content Discovery:**
- ✅ Today's devotional endpoint
- ✅ Feed with recent devotionals
- ✅ Calendar view
- ✅ Trending devotionals
- ✅ Series browsing

**Admin & Moderation:**
- ✅ Admin dashboard with stats
- ✅ Content moderation system
- ✅ Flag inappropriate content
- ✅ Moderation queue
- ✅ User management
- ✅ Platform settings

**Author Tools:**
- ✅ Author dashboard with analytics
- ✅ Performance metrics
- ✅ Engagement tracking
- ✅ Milestone tracking

**Groups & Community:**
- ✅ Create and manage groups
- ✅ Group invitations
- ✅ Member management
- ✅ Group devotionals

**Gamification:**
- ✅ Achievements system
- ✅ Badges and milestones
- ✅ Reading streaks
- ✅ Progress tracking

**Media & Storage:**
- ✅ Image upload (Hetzner WebDAV)
- ✅ Avatar uploads
- ✅ Cover image management
- ✅ **Pexels integration** with attribution

**Recent Additions (Dec 2025):**
- ✅ **Preview button** - See devotionals before publishing
- ✅ **Pexels stock photos** - Search and select free images
- ✅ **Series autocomplete** - Filter and search existing series
- ✅ **Reflection field** - Added dedicated reflection section to composer
- ✅ Fixed scripture field validation
- ✅ Fixed categories validator
- ✅ Fixed series API serialization
- ✅ Fixed reflection ReferenceError in preview
- ✅ Fixed pagination issue preventing devotionals from loading after deletion (Dec 20, 2025)
- ✅ Added freshmanna365.com domain with SSL (Dec 20, 2025)

### ⏳ Planned Features

**AI Features:**
- ⏳ Text-to-speech (OpenAI TTS)
- ⏳ AI-generated summaries
- ⏳ Scripture explanations

**Notifications:**
- ⏳ Push notifications (Firebase)
- ⏳ Email notifications
- ⏳ Daily devotional reminders

**Advanced Analytics:**
- ⏳ Detailed engagement metrics
- ⏳ Reader insights
- ⏳ Growth tracking

**Search:**
- ⏳ Full-text search
- ⏳ Advanced filters
- ⏳ Search autocomplete

---

## 🛠 Technology Stack

### Frontend (Implemented)

| Category | Technology |
|----------|-----------|
| **Framework** | React 18.3 + TypeScript |
| **Build Tool** | Vite 5.4 |
| **UI Library** | shadcn/ui with Radix UI primitives |
| **Styling** | Tailwind CSS 3.4 with custom spiritual theme |
| **Animations** | Framer Motion |
| **State Management** | TanStack React Query |
| **Routing** | React Router DOM v6 |
| **Forms** | React Hook Form + Zod validation |
| **Charts** | Recharts |
| **Icons** | Lucide React |
| **Fonts** | Cormorant Garamond (serif), DM Sans (sans) |

### Backend (Implemented)

| Category | Technology |
|----------|-----------|
| **Framework** | FastAPI |
| **Database** | MongoDB (127.0.0.1:27017/devotionalflow) |
| **Authentication** | Supabase Auth (supabase.ailabsafrica.com) |
| **Validation** | Pydantic V2 |
| **File Storage** | Hetzner Storage Box (WebDAV) |
| **Stock Photos** | Pexels API |
| **Scripture API** | API.Bible + ESV API |
| **Testing** | Pytest (in progress) |

### Infrastructure (Deployed)

- **Port**: 30042
- **Domain**: freshmanna.ailabsafrica.com
- **API Domain**: freshmanna-api.ailabsafrica.com
- **Reverse Proxy**: Nginx (configured with SSL)
- **SSL**: Let's Encrypt (expires Jan 2026)
- **Process Manager**: Systemd (`kasaai-devotionalflow-backend.service`)
- **Virtual Environment**: `/opt/kasaai/apps/venv` (shared)
- **Service Status**: ✅ Active and running

---

## 🚀 Getting Started

### Prerequisites

- **Node.js** 18+ and npm/yarn
- **Python** 3.11+
- **MongoDB** (running at 127.0.0.1:27017)
- **Supabase** account (for authentication)

### Installation

#### 1. Clone the Repository

```bash
cd /opt/kasaai/apps/devotionalflow
```

#### 2. Frontend Setup

```bash
cd frontend
npm install
```

Create `.env.dev` file:

```env
VITE_API_BASE_URL=http://localhost:30037
VITE_SUPABASE_URL=https://supabase.ailabsafrica.com
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
```

Run the frontend:

```bash
npm run dev
```

Frontend will be available at **http://localhost:8080**

#### 3. Backend Setup (Not Yet Implemented)

The backend needs to be built from scratch. When implemented:

```bash
cd backend

# Activate shared virtual environment
source /opt/kasaai/apps/venv/bin/activate

# Install dependencies (to be created)
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
MONGODB_URI=mongodb://admin:aawwER4444%@127.0.0.1:27017/
DATABASE_NAME=devotionalflow
SUPABASE_URL=https://supabase.ailabsafrica.com
SUPABASE_KEY=your_supabase_key
SUPABASE_JWT_SECRET=your_jwt_secret
OPENAI_API_KEY=your_openai_key
SECRET_KEY=your_secret_key
CORS_ORIGINS=["http://localhost:8080", "https://devotionalflow.ailabsafrica.com"]
EOF

# Run the backend (future)
uvicorn main:app --host 0.0.0.0 --port 30037 --reload
```

---

## 📂 Project Structure

### Frontend Structure

```
frontend/
├── src/
│   ├── pages/                    # Page components
│   │   ├── Index.tsx            # Landing page
│   │   ├── Auth.tsx             # Login/Signup
│   │   ├── Dashboard.tsx        # Pastor dashboard
│   │   ├── Compose.tsx          # Devotional editor
│   │   ├── Feed.tsx             # Reader feed
│   │   ├── Devotional.tsx       # Single devotional view
│   │   ├── Profile.tsx          # User profile
│   │   └── NotFound.tsx         # 404 page
│   │
│   ├── components/
│   │   ├── landing/             # Landing page sections
│   │   │   ├── Navbar.tsx
│   │   │   ├── Hero.tsx
│   │   │   ├── Features.tsx
│   │   │   ├── HowItWorks.tsx
│   │   │   ├── DevotionalPreview.tsx
│   │   │   ├── Pricing.tsx
│   │   │   └── Footer.tsx
│   │   │
│   │   └── ui/                  # shadcn/ui components (50+ components)
│   │       ├── button.tsx
│   │       ├── card.tsx
│   │       ├── input.tsx
│   │       └── ...
│   │
│   ├── App.tsx                  # Main app with routing
│   ├── main.tsx                 # Entry point
│   ├── index.css                # Global styles and theme
│   └── assets/                  # Images and media
│
├── package.json                 # Dependencies
├── vite.config.ts              # Vite configuration
├── tailwind.config.ts          # Tailwind + theme config
├── tsconfig.json               # TypeScript config
└── index.html                  # HTML entry point
```

### Backend Structure (Planned)

```
backend/
├── app/
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Configuration and settings
│   │
│   ├── models/                 # Pydantic models
│   │   ├── user.py
│   │   ├── devotional.py
│   │   ├── comment.py
│   │   ├── engagement.py
│   │   └── analytics.py
│   │
│   ├── routes/                 # API endpoints
│   │   ├── auth.py            # Authentication routes
│   │   ├── devotionals.py     # Devotional CRUD
│   │   ├── users.py           # User management
│   │   ├── comments.py        # Comments system
│   │   ├── engagement.py      # Likes, bookmarks, shares
│   │   ├── analytics.py       # Analytics endpoints
│   │   ├── ai.py              # AI features (TTS, summaries)
│   │   └── media.py           # File uploads
│   │
│   ├── services/               # Business logic
│   │   ├── auth_service.py    # Supabase integration
│   │   ├── devotional_service.py
│   │   ├── ai_service.py      # AI integrations
│   │   ├── scripture_service.py
│   │   ├── email_service.py
│   │   └── analytics_service.py
│   │
│   ├── db/                     # Database
│   │   ├── mongodb.py         # MongoDB connection
│   │   └── schemas.py         # MongoDB schemas
│   │
│   └── utils/                  # Utilities
│       ├── auth.py            # JWT helpers
│       ├── validators.py      # Custom validators
│       └── helpers.py
│
├── tests/                      # Unit and integration tests
│   ├── test_auth.py
│   ├── test_devotionals.py
│   ├── test_comments.py
│   └── test_ai.py
│
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables
└── README.md                   # Backend documentation
```

---

## 🎨 Design System

### Color Palette

The spiritual color palette creates a calming, uplifting atmosphere:

| Color | Hex | Purpose |
|-------|-----|---------|
| **Deep Navy** | `#1a2332` | Trust, depth, spirituality |
| **Soft Gold** | `#d4a650` | Divine, warmth, enlightenment |
| **Teal** | `#2d7c7c` | Hope, renewal, calm |
| **Cream** | `#f8f6f3` | Clean background, peace |

### Typography

- **Headings**: Cormorant Garamond (serif) - Elegant, readable, spiritual feel
- **Body Text**: DM Sans (sans-serif) - Modern, clean, highly readable

### Visual Style

- Smooth animations with Framer Motion (fade, slide, float effects)
- Subtle gradients and glows for depth
- Generous white space for calm reading
- Card-based layouts with soft shadows
- Responsive grid system

---

## ✨ Features Overview

### For Pastors (Content Creators)

#### 1. **Devotional Composer**
- Rich text editor with formatting tools (bold, italic, lists, quotes)
- Scripture block insertion with auto-lookup
- Image upload for cover and inline images
- Audio upload or recording
- Video upload (optional)
- Category tagging (Faith, Purpose, Prayer, Wisdom, Love, Hope, Gratitude, Forgiveness)
- Draft autosave
- Schedule publishing for future dates

#### 2. **Dashboard**
- Overview stats: Total Readers, Devotionals Published, Engagement Rate, This Week's Views
- Recent devotionals list with engagement metrics (views, likes, comments)
- Quick actions (Compose New, View Calendar, Settings)
- Sidebar navigation

#### 3. **Calendar View**
- Monthly calendar showing published and scheduled devotionals
- Drag-and-drop scheduling
- Quick edit and preview

#### 4. **Analytics** (Future)
- Engagement trends over time
- Top-performing devotionals
- Reader demographics and behavior
- Reading time analytics
- Share and bookmark rates

#### 5. **Settings**
- Profile management (bio, photo, ministry info)
- Branding customization (Pro plan)
- Notification preferences
- Account management

### For Readers (Consumers)

#### 1. **Feed**
- Today's featured devotional
- Recent devotionals list
- Personalized recommendations
- Filter by category

#### 2. **Reading Experience**
- Clean, distraction-free reading mode
- Adjustable font size
- Light/dark theme toggle (planned)
- Scripture reference popups
- Audio playback (TTS or uploaded)
- Continue reading where you left off
- Smooth page transitions

#### 3. **Engagement**
- Like devotionals and comments
- Comment and reply to discussions
- Bookmark favorites for later
- Share to WhatsApp, Facebook, Twitter, Instagram
- Report inappropriate content

#### 4. **Profile**
- Reading stats: Devotionals Read, Day Streak, Bookmarked, Liked
- Reading history with dates
- Bookmarks collection
- Edit profile and preferences
- Sign out

#### 5. **Discovery** (Future)
- Browse by date, topic, scripture reference
- Search keywords and verses
- Random devotional for inspiration
- Yearly devotional index

### AI Features

#### Phase 1 (MVP)
- **AI Text-to-Speech**: Convert devotionals to natural-sounding audio
- **AI Summary**: One-paragraph quick summary for busy readers
- **AI Scripture Explanation**: Tap any verse for historical context and meaning

#### Phase 2 (Future)
- **AI Spiritual Companion**: Conversational assistant that:
  - Suggests relevant devotionals based on user's spiritual journey
  - Answers questions about faith and scripture
  - Guides prayer and reflection
  - Trained on pastor's devotionals (pastor controls boundaries)

---

## 🗺 Development Roadmap

### Phase 1: MVP Backend Foundation (6-8 weeks)

**Goal**: Get the core platform functional with authentication and basic devotional publishing.

**Deliverables**:
- ✅ FastAPI application structure
- ✅ MongoDB database setup with schemas
- ✅ Supabase authentication integration (email, Google, Apple)
- ✅ User CRUD (create, read, update, delete)
- ✅ Devotional CRUD with draft/published states
- ✅ Basic pastor dashboard APIs
- ✅ Reader feed APIs
- ✅ Comments system (create, read, delete)
- ✅ Likes and bookmarks
- ✅ File upload for images
- ✅ Basic analytics (view counts, engagement counts)
- ✅ Unit tests for all CRUD operations
- ✅ Frontend integration (replace mock data with real API calls)

**Success Metrics**:
- Backend returns real data to frontend
- Pastors can create, edit, and publish devotionals
- Readers can view, like, comment, and bookmark
- Authentication works end-to-end

---

### Phase 2: Core Features (4-6 weeks)

**Goal**: Add AI features and engagement tools to enhance the user experience.

**Deliverables**:
- ✅ AI TTS integration (OpenAI or ElevenLabs)
- ✅ Scripture API integration (Bible verse lookup and display)
- ✅ Search functionality (full-text search on devotionals)
- ✅ Reading history tracking
- ✅ Push notification system
- ✅ Email notifications (new devotional, replies)
- ✅ Advanced analytics dashboard
  - Engagement trends
  - Top devotionals
  - Reader retention
- ✅ Calendar scheduling system
- ✅ Audio player with progress tracking
- ✅ Dark mode toggle

**Success Metrics**:
- Audio narration works for all devotionals
- Scripture references display correctly
- Search returns relevant results
- Pastors receive engagement insights

---

### Phase 3: AI Enhancement (4-6 weeks)

**Goal**: Elevate the spiritual experience with advanced AI capabilities.

**Deliverables**:
- ✅ AI summary generation (one-paragraph summaries)
- ✅ AI scripture explanations (context and historical background)
- ✅ AI writing assistance for pastors (suggestions, scripture recommendations)
- ✅ Enhanced recommendation engine (personalized devotionals)
- ✅ Audio player enhancements (speed control, offline download)
- ✅ Social sharing templates (Instagram, Facebook, WhatsApp)
- ✅ Reading streak tracking and gamification

**Success Metrics**:
- AI summaries are accurate and helpful
- Scripture explanations add value
- Recommendation engine increases engagement
- Users return daily (tracked by streak)

---

### Phase 4: Advanced Features (6-8 weeks)

**Goal**: Scale the platform with multi-pastor support, monetization, and community features.

**Deliverables**:
- ✅ AI Interactive Spiritual Assistant
  - Conversational interface
  - Answers spiritual questions
  - Recommends devotionals
  - Guides prayer and reflection
- ✅ Multi-pastor organization support
  - Team accounts
  - Role management (admin, editor, contributor)
  - Content approval workflow
- ✅ Live audio/video broadcasts
- ✅ Prayer groups and communities
  - Create groups
  - Group discussions
  - Prayer request boards
- ✅ Donation integration
  - Mobile Money (MoMo) for African market
  - Stripe, PayPal
  - "Support the Ministry" button
- ✅ Advanced customization
  - Custom themes and branding
  - Custom domain (Ministry plan)
  - White-label option
- ✅ Mobile apps (React Native)
  - iOS and Android native apps
  - Push notifications
  - Offline reading

**Success Metrics**:
- Multiple pastors using organization accounts
- Donations flowing to pastors
- High engagement in prayer communities
- Mobile app downloads and retention

---

## 📊 Success Metrics

### Pastor KPIs
- **Devotionals Published**: Number of devotionals published per month
- **Daily Active Creators**: Pastors publishing regularly
- **Paid Account Retention**: Percentage of pastors renewing Pro/Ministry plans
- **Engagement Rate**: Likes/comments per 100 readers

### Reader KPIs
- **Daily Active Readers**: Users reading devotionals daily
- **Time Spent Reading**: Average reading duration
- **Audio Listen Rate**: Percentage of users listening vs reading
- **Share Rate**: Shares to WhatsApp, Facebook, etc. (critical for African market)
- **Returning User Rate**: 7-day and 30-day return rate

### Business KPIs
- **Monthly Recurring Revenue (MRR)**: From Pro and Ministry subscriptions
- **Customer Acquisition Cost (CAC)**: Marketing spend per new pastor
- **Lifetime Value (LTV)**: Average revenue per pastor over lifetime
- **Churn Rate**: Percentage of pastors canceling subscriptions
- **Free-to-Paid Conversion**: Percentage of free users upgrading

---

## 🔐 Security & Compliance

- **Authentication**: Supabase with OAuth (Google, Apple, email/password)
- **Authorization**: Role-based access control (Pastor, Reader, Admin)
- **API Security**: JWT tokens, rate limiting, CORS
- **Data Encryption**: HTTPS/TLS, encrypted passwords (bcrypt)
- **GDPR Compliance**: Data export, deletion, consent management
- **Content Moderation**: Report system for abusive content
- **Pastor Verification**: Optional MFA for pastor accounts

---

## 🧪 Testing Strategy

Following the pattern from `/opt/kasaai/apps/core_backend/TEST_SUITE_ANALYSIS.md`:

### Backend Tests (Required)

**Unit Tests** (`tests/test_*.py`):
- Test each CRUD operation with real database
- Test authentication flows (signup, login, logout, password reset)
- Test AI services (TTS, scripture lookup, summarization)
- Test validation and error handling
- Test edge cases and failure scenarios

**Integration Tests**:
- End-to-end API tests
- Database integration tests (create, read, update, delete with real data)
- Supabase authentication integration
- File upload and retrieval

**Test Coverage**:
- Minimum 80% code coverage
- All critical paths covered
- No mocked database for CRUD tests

**CI/CD**:
- Run tests on every commit
- Block merges if tests fail
- Track coverage over time

### Frontend Tests (Optional)

- Component tests with React Testing Library
- E2E tests with Playwright (for critical flows)

---

## 🤝 Contributing

### Code Style

**Python (Backend)**:
- Follow PEP8
- Use type hints
- Format with `black`
- Use Pydantic for validation
- Write docstrings for every function (Google style)

**TypeScript (Frontend)**:
- Follow ESLint rules
- Use TypeScript strict mode
- Prefer functional components with hooks
- Use Zod for validation
- Keep components under 300 lines

### File Organization

- **Never create files longer than 500 lines**
- Split large files into modules
- Group by feature, not by type
- Use clear, consistent imports

### Testing Requirements

- **Always create unit tests for new features**
- At least 1 test for expected use, 1 edge case, 1 failure case
- Use real database for CRUD tests, not mocks
- Update existing tests when modifying logic

### Commit Guidelines

- Use conventional commits: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`
- Create a git commit after each completed task
- Write clear commit messages explaining the "why"

---

## 📝 Environment Variables

### Backend `.env`

```bash
# Database
MONGODB_URI=mongodb://admin:aawwER4444%@127.0.0.1:27017/
DATABASE_NAME=devotionalflow

# Supabase Authentication
SUPABASE_URL=https://supabase.ailabsafrica.com
SUPABASE_KEY=your_supabase_service_key
SUPABASE_JWT_SECRET=your_jwt_secret

# AI Services
OPENAI_API_KEY=your_openai_api_key
ELEVENLABS_API_KEY=your_elevenlabs_key  # Optional

# Scripture API
BIBLE_API_KEY=your_bible_api_key

# Email Service
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# File Storage
S3_BUCKET=devotionalflow-media
S3_ACCESS_KEY=your_s3_access_key
S3_SECRET_KEY=your_s3_secret_key
S3_REGION=us-east-1

# Application
SECRET_KEY=your_random_secret_key_here
CORS_ORIGINS=["http://localhost:8080", "https://devotionalflow.ailabsafrica.com"]
PORT=30037

# Push Notifications (Future)
FIREBASE_PROJECT_ID=your_firebase_project_id
FIREBASE_PRIVATE_KEY=your_firebase_private_key
```

### Frontend `.env.dev`

```bash
VITE_API_BASE_URL=http://localhost:30037
VITE_SUPABASE_URL=https://supabase.ailabsafrica.com
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
```

---

## 🚀 Deployment

### Infrastructure Setup (To Be Configured)

Based on the pattern from `/opt/kasaai/CLAUDE.md`:

**1. Backend Service**:
```bash
# Port allocation
PORT=30037

# Systemd service
/etc/systemd/system/kasaai-devotionalflow-backend.service

# Nginx reverse proxy
/etc/nginx/sites-available/devotionalflow-api.ailabsafrica.com.conf

# SSL certificate
sudo certbot --nginx -d devotionalflow-api.ailabsafrica.com
```

**2. Frontend Service**:
```bash
# Build frontend
cd /opt/kasaai/apps/devotionalflow/frontend
npm run build

# Nginx static files
/etc/nginx/sites-available/devotionalflow.ailabsafrica.com.conf

# SSL certificate
sudo certbot --nginx -d devotionalflow.ailabsafrica.com
```

**3. MongoDB Database**:
```bash
# Database: devotionalflow
# Uses shared MongoDB at 127.0.0.1:27017
# Credentials in /opt/kasaai/.env
```

**4. Shared Virtual Environment**:
```bash
# Backend uses shared venv at /opt/kasaai/apps/venv
source /opt/kasaai/apps/venv/bin/activate
```

**5. Service Management**:
```bash
# Start service
sudo systemctl start kasaai-devotionalflow-backend

# Enable on boot
sudo systemctl enable kasaai-devotionalflow-backend

# View logs
sudo journalctl -u kasaai-devotionalflow-backend -f

# Reload nginx
sudo systemctl reload nginx
```

---

## 🔧 Recent Fixes

### Admin Panel Sort by Title Fix (2025-12-20)
**Issue**: Frontend was sending `sort_by=title` to the API, but the backend only supports: `created_at`, `published_at`, `views_count`, `likes_count`. This caused a 422 validation error when clicking the "Title" column header in the admin content table.

**Solution**: Implemented client-side sorting for the title column. When users click the "Title" header:
1. Frontend fetches data using `sort_by=created_at` (valid backend parameter)
2. Results are sorted alphabetically by title on the client-side
3. Sort order (asc/desc) is respected

**Files Modified**: `devotionalflow/frontend/src/pages/admin/AdminContent.tsx`

---

## 📚 Related Documentation

- **PRD (Product Requirements Document)**: [PRD.md](./PRD.md)
- **Implementation Status**: [IMPLEMENTATION_STATUS.md](./IMPLEMENTATION_STATUS.md)
- **Infrastructure Guide**: `/opt/kasaai/CLAUDE.md`
- **Test Suite Analysis**: `/opt/kasaai/apps/core_backend/TEST_SUITE_ANALYSIS.md`

---

## 🌍 Similar Apps in Infrastructure

DevotionalFlow follows the same architectural pattern as:

- **ChurchFlow** (`/opt/kasaai/apps/churchflow/`): Similar church management focus
- **StudyFlow** (`/opt/kasaai/apps/studyflow/`): Education platform with similar stack
- **EventFlow** (`/opt/kasaai/apps/eventflow/`): Event management with MongoDB + FastAPI

All apps share:
- Supabase authentication
- MongoDB database
- FastAPI backend
- React + Vite frontend
- Nginx + SSL infrastructure

---

## 📧 Support & Contact

For questions, issues, or contributions:

- **Project Lead**: AI Labs Africa
- **Email**: admin@ailabsafrica.com
- **Infrastructure Documentation**: `/opt/kasaai/CLAUDE.md`

---

## 📄 License

MIT License - see LICENSE file for details

---

## 🙏 Acknowledgments

- **shadcn/ui**: For the beautiful UI component library
- **Radix UI**: For accessible primitives
- **Framer Motion**: For smooth animations
- **Tailwind CSS**: For the utility-first styling system
- **FastAPI**: For the high-performance Python framework
- **MongoDB**: For flexible document storage
- **Supabase**: For authentication and real-time features

---

**Built with ❤️ for pastors and spiritual communities worldwide**

**Status**: Frontend Complete | Backend Pending Implementation
