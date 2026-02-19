# FreshManna - Daily Devotional Community

A modern Progressive Web App (PWA) designed to deepen your faith through daily devotionals, scripture study, and community engagement.

## Overview

FreshManna provides a spiritual community platform where users can engage with daily devotionals throughout the year, connect with fellow believers through Bible study groups, and grow in their faith journey. The app combines modern technology with timeless spiritual practices to create an engaging and accessible devotional experience.

## Key Features

### 1. Daily Devotionals
- **365 Devotionals**: A unique devotional entry for each day of the year
- **Structured Content**: Each devotional includes:
  - Scripture reference
  - Thoughtful reflection
  - Guided prayer
- **Reading Tracking**: Track your daily reading progress and streaks
- **Bookmarks**: Save favorite devotionals for later reflection

### 2. Scripture Integration
- **Clickable References**: Click any scripture reference to view the full Bible text
- **Multiple Translations**: Support for NIV, KJV, ESV, and other popular Bible versions
- **Bible API Integration**: Real-time access to scripture without switching apps
- **Context Viewing**: See surrounding verses for better understanding

### 3. Bible Study Groups
- **Create or Join Groups**: Form communities around shared spiritual interests
- **Group Discussions**: Dedicated discussion threads for each day's devotional
- **Chat Functionality**: Real-time messaging to share insights and encouragement
- **Topic-Based Studies**: Organize studies around specific themes or books of the Bible
- **Prayer Requests**: Share and pray for group members' needs

### 4. Social Engagement
- **Comments**: Reflect and discuss devotionals with the community
- **Likes & Reactions**: Show appreciation for insights and prayers
- **Social Sharing**: Share devotionals to Facebook, Twitter, WhatsApp, and email
- **Community Feed**: See what others are reading and reflecting on

### 5. User Profiles
- **Personal Dashboard**: Track your spiritual journey
- **Reading History**: See all devotionals you've engaged with
- **Progress Tracking**: Monitor reading streaks and completed devotionals
- **Saved Content**: Access bookmarked devotionals and favorite scriptures
- **Achievement Badges**: Earn badges for consistent engagement

### 6. Notifications & Reminders
- **Daily Devotional Reminders**: Never miss a day with customizable notifications
- **Group Activity Alerts**: Get notified of new discussions in your groups
- **Prayer Request Updates**: Stay informed about group prayer needs
- **Scripture of the Day**: Morning inspiration delivered to your device

### 7. Offline Access (PWA)
- **Download Devotionals**: Save content for offline reading
- **Progressive Web App**: Install on any device (iOS, Android, Desktop)
- **Offline Mode**: Access downloaded content without internet
- **Background Sync**: Automatically sync when connection returns
- **Service Worker Caching**: Fast loading even on slow connections

### 8. Content Management (Admin)
- **Devotional Creation**: Rich text editor with scripture integration
- **Content Scheduling**: Plan and schedule devotionals in advance
- **Media Support**: Add images, audio, and video to devotionals
- **Draft Management**: Save and edit drafts before publishing
- **Analytics Dashboard**: Track engagement and reach

## Technical Stack

### Frontend
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite 5.4
- **UI Components**: shadcn/ui + Tailwind CSS
- **Animations**: Framer Motion
- **State Management**: React Query (TanStack Query)
- **PWA**: vite-plugin-pwa + Workbox
- **Offline Storage**: IndexedDB (idb)

### Mobile Features
- **Responsive Design**: Mobile-first approach with breakpoints
- **Touch Gestures**:
  - Pull-to-refresh
  - Swipe navigation
  - Long-press actions
- **Native Feel**: iOS and Android optimizations
- **Installation**: Add to Home Screen prompts

### Backend Integration
- **API Client**: Axios with automatic token refresh
- **Authentication**: JWT-based auth with Supabase
- **Real-time**: WebSocket support for chat and notifications
- **Bible API**: Integration with Bible API for scripture lookups
- **Database**: MongoDB for devotionals and user data

## Design Philosophy

### Spiritual & Uplifting Theme
- **Color Palette**: Navy (#2B3A52), Gold (#D4A455), Teal (#2D7C7C), Cream (#FBF8F3)
- **Typography**:
  - Serif (Cormorant Garamond) for headings
  - Sans-serif (DM Sans) for body text
- **Spiritual Symbolism**: Open book and cross imagery throughout
- **Clean & Modern**: Minimalist design that doesn't distract from content

### User Experience
- **Intuitive Navigation**: Easy access to daily devotionals, groups, and profile
- **Fast Loading**: Optimized bundle size (200 KB gzipped)
- **Accessible**: WCAG 2.1 AA compliant
- **Dark Mode Ready**: Support for light and dark themes

## Project Structure

```
frontend/
├── public/
│   ├── icons/              # PWA icons (72x72 to 512x512)
│   └── manifest.webmanifest
├── src/
│   ├── components/
│   │   ├── landing/        # Landing page components
│   │   ├── pwa/            # PWA-specific (install, offline, update)
│   │   ├── mobile/         # Mobile UX (pull-to-refresh, swipeable)
│   │   ├── loading/        # Skeleton loaders
│   │   └── ui/             # shadcn components
│   ├── pages/
│   │   ├── Landing.tsx     # Public landing page
│   │   ├── Auth.tsx        # Login/Signup
│   │   ├── Feed.tsx        # Daily devotionals feed
│   │   ├── Devotional.tsx  # Single devotional view
│   │   ├── Profile.tsx     # User profile & bookmarks
│   │   └── Dashboard.tsx   # Admin/Pastor dashboard
│   ├── lib/
│   │   ├── api.ts          # API client
│   │   └── db.ts           # IndexedDB wrapper
│   ├── hooks/
│   │   ├── useOfflineSync.ts
│   │   └── useLongPress.ts
│   ├── contexts/
│   │   └── AuthContext.tsx
│   └── main.tsx
├── vite.config.ts
├── tailwind.config.ts
└── postcss.config.js
```

## Getting Started

### Prerequisites
- Node.js 18+ and npm
- Git

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd devotionalflow/frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The app will be available at `http://localhost:8080`

### Build for Production

```bash
# Create production build
npm run build

# Preview production build
npm run preview
```

### PWA Testing

To test PWA features:

1. Build the production version: `npm run build`
2. Serve with HTTPS (required for service workers)
3. Install the app from browser menu
4. Test offline by disabling network in DevTools

## Environment Variables

Create a `.env` file in the frontend directory:

```env
VITE_API_URL=https://devotionalflow-api.ailabsafrica.com
VITE_BIBLE_API_KEY=your_bible_api_key
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_key
```

## User Roles

### Regular User
- View and read daily devotionals
- Comment and like devotionals
- Join Bible study groups
- Bookmark favorite content
- Track reading progress
- Share devotionals
- Receive daily notifications

### Pastor/Admin
- All regular user features
- Create and edit devotionals
- Schedule future devotionals
- Manage content (drafts, published, archived)
- View analytics and engagement metrics
- Moderate group discussions
- Manage user reports

## Performance

- **Lighthouse PWA Score**: 95+ target
- **First Contentful Paint**: < 2s
- **Time to Interactive**: < 3.5s
- **Bundle Size**: 652 KB (200 KB gzipped)
- **Precached Assets**: 87 files (1.68 MB)

## Browser Support

- Chrome/Edge (latest 2 versions)
- Firefox (latest 2 versions)
- Safari (latest 2 versions)
- iOS Safari 12+
- Chrome Android 90+

## Contributing

This is a private project. For questions or feature requests, please contact the development team.

## License

Proprietary - All rights reserved

## Contact

For support or inquiries, contact: admin@ailabsafrica.com

---

**Built with ❤️ for spiritual growth and fellowship**
