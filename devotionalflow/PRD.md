# DevotionalFlow - Product Requirements Document (PRD)

**Version**: 1.0
**Last Updated**: December 9, 2025
**Status**: Pre-Development (Frontend Complete, Backend Pending)

---

## 📋 Table of Contents

1. [Product Vision](#product-vision)
2. [User Personas](#user-personas)
3. [Core Features](#core-features)
4. [AI Features](#ai-features)
5. [Technical Requirements](#technical-requirements)
6. [Design Requirements](#design-requirements)
7. [Subscription Model](#subscription-model)
8. [Success Metrics](#success-metrics)
9. [Implementation Roadmap](#implementation-roadmap)
10. [User Stories](#user-stories)
11. [Risks & Mitigations](#risks--mitigations)
12. [Dependencies](#dependencies)

---

## 1. Product Vision

### Mission Statement

**To empower pastors with a simple yet powerful platform to publish devotionals and spiritual messages daily, nurturing a digital community around their ministry and transforming how spiritual content reaches and engages people in the digital age.**

### Target Market

**Primary Market**: African pastors and churches
- Growing smartphone adoption in Africa
- WhatsApp-first communication culture
- Mobile money integration (MoMo) for monetization
- Strong community-oriented spiritual culture

**Secondary Market**: Global pastors and spiritual leaders
- Digital-first churches
- Online ministry platforms
- Multi-site congregations
- Para-church organizations

### Market Opportunity

**Problem Statement**:
1. Pastors lack simple, beautiful tools to publish daily devotionals
2. Traditional methods (email, PDF, social media) are fragmented and non-engaging
3. No analytics to understand audience engagement
4. Difficult to build and maintain digital communities
5. Time-consuming to manage daily content

**Solution**:
DevotionalFlow provides:
- Beautiful, mobile-first devotional publishing platform
- AI-powered features (TTS, summaries, scripture lookup)
- Built-in community engagement (comments, likes, shares)
- Analytics to track impact
- Scheduling to save time
- Monetization options to sustain ministry

### Value Proposition

**For Pastors**:
- "Publish beautiful devotionals in minutes, not hours"
- Schedule weeks of content in advance
- Reach your congregation where they are (mobile)
- Track engagement and understand your audience
- Build a loyal digital community
- Monetize your ministry sustainably

**For Readers**:
- "Experience daily spiritual growth with beautifully crafted devotionals"
- Listen to audio narrations while commuting
- Engage with a spiritual community
- Access devotionals anywhere, anytime
- Discover relevant content easily
- Track your spiritual journey with streaks and history

---

## 2. User Personas

### Persona 1: Pastor David (Content Creator)

**Demographics**:
- Age: 35-55
- Location: Nairobi, Kenya
- Role: Senior Pastor, mid-sized church (200-500 members)
- Tech Savvy: Moderate (uses smartphone daily, social media comfortable)

**Pain Points**:
- ⏰ Spends 2+ hours daily on devotional distribution (email, WhatsApp groups, Facebook)
- 📊 No visibility into who's reading or engaging with content
- 📱 Content looks unprofessional on different platforms
- 🔄 Repetitive daily publishing process
- 💰 Limited budget for ministry tools

**Goals**:
- 🎯 Reach more people beyond Sunday services
- 📈 Grow digital congregation
- 💬 Build deeper relationships with members
- ⏱️ Save time on content distribution
- 📊 Understand what messages resonate most
- 💵 Generate income to support full-time ministry

**How DevotionalFlow Helps**:
- Publish once, reach all platforms
- Beautiful, branded devotional pages
- Analytics dashboard showing engagement
- Schedule weeks of content in advance
- Subscription revenue from Pro plan
- AI assistance for faster writing

### Persona 2: Grace (Regular Reader)

**Demographics**:
- Age: 28-45
- Location: Lagos, Nigeria
- Occupation: Professional (marketing manager, teacher, nurse)
- Tech Savvy: High (smartphone power user, social media native)

**Pain Points**:
- ⏰ Busy schedule makes consistent spiritual practice difficult
- 📱 Devotional content scattered across email, WhatsApp, apps
- 🔇 Prefers audio when commuting but most content is text-only
- 🤝 Feels isolated in spiritual journey, lacks community
- 📖 Wants deeper understanding of scripture references

**Goals**:
- 🙏 Daily spiritual growth and consistency
- 🎧 Consume content while multitasking (commute, exercise)
- 💬 Connect with others on similar spiritual journey
- 📚 Understand biblical context better
- ⭐ Revisit meaningful messages easily
- 📈 Track spiritual progress and growth

**How DevotionalFlow Helps**:
- One beautiful app for all spiritual content
- AI-narrated audio for every devotional
- Comment and engage with community
- Scripture explanations with one tap
- Bookmark and organize favorite devotionals
- Reading streaks to maintain consistency

### Persona 3: Bishop Emmanuel (Multi-Pastor Organization)

**Demographics**:
- Age: 50-65
- Location: Accra, Ghana
- Role: Presiding Bishop, multi-site church network (10+ branches, 5,000+ members)
- Tech Savvy: Moderate (delegates technical tasks)

**Pain Points**:
- 🏢 Managing content across multiple pastors and locations
- ✅ Quality control and approval workflow needed
- 📊 Consolidated analytics for entire network
- 🎨 Consistent branding across all content
- 💰 Budget for ministry tools across multiple sites

**Goals**:
- 🎯 Unified content platform for all branches
- 👥 Empower individual pastors to publish while maintaining oversight
- 📊 Track engagement across entire network
- 🏷️ Consistent branding and messaging
- 💵 Monetize content to fund ministry operations

**How DevotionalFlow Helps**:
- Ministry plan with multi-pastor support
- Role-based permissions (admin, editor, contributor)
- Content approval workflow
- Consolidated analytics dashboard
- Custom branding and domain
- Team billing and management

---

## 3. Core Features

### 3.1 Pastor Features (Content Creator)

#### A. Devotional Composer

**Priority**: P0 (Must-Have for MVP)

**Description**: A beautiful, distraction-free writing environment for creating devotionals.

**Functional Requirements**:

1. **Rich Text Editor**
   - Formatting tools: Bold, Italic, Underline, Strikethrough
   - Paragraph styles: Heading 1, Heading 2, Heading 3, Paragraph, Quote
   - Lists: Bulleted, Numbered
   - Text alignment: Left, Center, Right
   - Link insertion
   - Undo/Redo

2. **Scripture Block Insertion**
   - Type scripture reference (e.g., "John 3:16")
   - Auto-suggest verses as you type
   - Fetch and insert full verse text
   - Format scripture in styled block with reference
   - Support multiple translations (KJV, NIV, ESV, NKJV)

3. **Media Upload**
   - Cover image upload (16:9 aspect ratio recommended)
   - Inline image insertion
   - Audio upload (MP3, M4A, WAV)
   - Video upload (MP4, MOV - optional)
   - Drag-and-drop support
   - Image cropping and resizing
   - Progress indicator for uploads

4. **Category & Tagging**
   - Pre-defined categories: Faith, Purpose, Prayer, Wisdom, Love, Hope, Gratitude, Forgiveness, Courage, Patience
   - Multi-select categories
   - Custom tags (Pro plan)

5. **Draft Management**
   - Auto-save every 30 seconds
   - Manual save button
   - Save as draft
   - Version history (Pro plan)

6. **Publishing Options**
   - Publish immediately
   - Schedule for future date/time
   - Save as draft
   - Preview before publishing
   - Edit after publishing

7. **Writing Assistance (Future - AI)**
   - Scripture suggestions based on content
   - Grammar and style suggestions
   - Tone analysis (encouraging, challenging, comforting)
   - Alternative phrasing suggestions

**Non-Functional Requirements**:
- Auto-save must not interrupt typing flow
- Editor must be fully responsive (mobile and desktop)
- Support keyboard shortcuts (Ctrl+B for bold, etc.)
- Load time < 1 second

**User Interface**:
- Clean, minimal toolbar
- Full-screen mode toggle
- Word count and reading time estimate
- Save status indicator ("Saving...", "Saved", "Failed")

**Success Metrics**:
- Average time to create devotional < 15 minutes
- Drafts saved successfully 99%+ of the time
- User satisfaction score 4.5+ out of 5

---

#### B. Devotional Management

**Priority**: P0 (Must-Have for MVP)

**Description**: Manage all devotionals in one place with calendar and list views.

**Functional Requirements**:

1. **Calendar View**
   - Monthly calendar grid
   - Color-coded status: Published (green), Scheduled (blue), Draft (gray)
   - Click date to view/edit devotional
   - Drag-and-drop to reschedule (Pro plan)
   - Multi-month view
   - Export calendar (iCal format - Pro plan)

2. **List View**
   - Table with columns: Title, Status, Date, Views, Likes, Comments
   - Sort by: Date, Title, Views, Engagement
   - Filter by: Status (All, Published, Scheduled, Draft), Category
   - Search by title or content
   - Bulk actions: Delete, Change category, Publish (Pro plan)
   - Pagination (20 per page)

3. **Devotional Actions**
   - Edit: Open in composer
   - Duplicate: Create copy as draft
   - Delete: Soft delete with confirmation
   - Preview: View as reader would see
   - View analytics: Detailed engagement stats
   - Share link: Copy shareable URL

4. **Bulk Import (Future)**
   - Upload CSV or Excel with devotionals
   - Map columns to fields (title, content, date, category)
   - Validate and preview before import
   - Import as drafts or scheduled

**Non-Functional Requirements**:
- List view loads < 2 seconds for 1,000+ devotionals
- Calendar renders smoothly without lag
- Search returns results in < 500ms

**User Interface**:
- Toggle between calendar and list views
- Consistent action buttons (edit, delete, duplicate)
- Confirmation dialogs for destructive actions
- Loading skeletons while fetching data

**Success Metrics**:
- Pastors can find any devotional in < 10 seconds
- 80%+ of pastors use calendar view for scheduling
- < 1% accidental deletions

---

#### C. Engagement Dashboard

**Priority**: P1 (High Priority, Post-MVP)

**Description**: Analytics and insights into reader engagement and devotional performance.

**Functional Requirements**:

1. **Overview Stats (Top Cards)**
   - Total Readers (unique users who viewed any devotional)
   - Devotionals Published (total count)
   - Average Engagement Rate (% of readers who liked/commented)
   - This Week's Views (compared to last week)

2. **Engagement Trends**
   - Line chart: Views over time (daily, weekly, monthly)
   - Line chart: Engagement over time (likes, comments, shares)
   - Compare multiple time periods
   - Export chart as image (Pro plan)

3. **Top-Performing Devotionals**
   - Table: Top 10 by views, likes, comments, shares
   - Thumbnail, title, publish date, engagement metrics
   - Click to view full devotional

4. **Reader Insights**
   - **Returning Readers**: Percentage who read 2+ devotionals
   - **Average Time Spent**: Reading duration per devotional
   - **Device Breakdown**: Mobile vs Desktop vs Tablet
   - **Time of Day**: When readers are most active
   - **Geographic Heatmap** (Pro plan): Country/city distribution
   - **Referral Sources** (Pro plan): Direct, social media, search

5. **Engagement Breakdown**
   - Likes per devotional (average, median, top)
   - Comments per devotional
   - Shares by platform (WhatsApp, Facebook, Twitter, Instagram)
   - Bookmarks

6. **Audience Growth**
   - New readers this week/month
   - Reader retention rate (% still reading after 30 days)
   - Churn rate

**Non-Functional Requirements**:
- Dashboard loads in < 3 seconds
- Data refreshes daily (not real-time for MVP)
- Support up to 1M data points efficiently

**User Interface**:
- Interactive charts (hover to see details)
- Date range selector (Last 7 days, 30 days, 90 days, All time, Custom)
- Export button for CSV reports (Pro plan)

**Success Metrics**:
- 70%+ of pastors check dashboard weekly
- Pastors report insights influence content strategy

---

#### D. Push Notifications

**Priority**: P2 (Nice-to-Have, Post-MVP)

**Description**: Send push notifications to readers for new devotionals and announcements.

**Functional Requirements**:

1. **Notification Types**
   - **New Devotional**: Automatically sent when devotional published
   - **Custom Announcement**: Manual message to all or segment of readers
   - **Scheduled Reminder**: Daily reminder at user's preferred time

2. **Notification Composer**
   - Title (50 chars max)
   - Message (150 chars max)
   - Deep link to devotional or custom URL
   - Preview how it will appear on mobile
   - Send immediately or schedule

3. **Audience Targeting**
   - All readers
   - Active readers (read in last 7 days)
   - Inactive readers (haven't read in 7+ days)
   - Custom segment by location, device, engagement

4. **Notification Settings (Pastor)**
   - Enable/disable auto-notifications for new devotionals
   - Default send time for new devotionals
   - Notification frequency cap (max per day/week)

5. **Reader Notification Preferences**
   - Enable/disable notifications
   - Preferred time (morning, afternoon, evening, custom)
   - Frequency (daily, weekly, never)
   - Notification sound

**Non-Functional Requirements**:
- Notifications delivered within 1 minute of sending
- Support for iOS and Android
- Delivery rate > 95%

**User Interface**:
- Simple notification composer
- Preview on iOS and Android mockups
- Delivery status (sent, delivered, opened)

**Success Metrics**:
- Open rate > 30%
- Opt-out rate < 5%

---

### 3.2 Reader Features (Consumer)

#### A. Home Feed

**Priority**: P0 (Must-Have for MVP)

**Description**: Personalized feed showing today's devotional and recent posts.

**Functional Requirements**:

1. **Today's Devotional**
   - Featured card at top of feed
   - Large hero image
   - Title, excerpt (first 100 chars)
   - Author name and photo
   - "Read Now" button
   - Reading time estimate
   - Audio badge if available

2. **Recent Devotionals**
   - List of recent devotionals (last 30 days)
   - Card layout: Thumbnail, title, author, date, category
   - Infinite scroll or pagination
   - Sort by: Latest, Popular, Trending
   - Filter by category

3. **Recommended Devotionals (Future - AI)**
   - Personalized recommendations based on:
     - Previously read devotionals
     - Liked/bookmarked content
     - Reading history
     - Similar users' preferences
   - "Because you read..." section

4. **Weekly Reflection (Future)**
   - Summary of past week's devotionals
   - Key themes
   - Most impactful verse
   - Reading streak progress

**Non-Functional Requirements**:
- Feed loads in < 2 seconds
- Images lazy-load for performance
- Smooth infinite scroll

**User Interface**:
- Clean, card-based layout
- Generous white space
- Sticky "Today's Devotional" when scrolling (optional)

**Success Metrics**:
- 70%+ of readers start from home feed
- Average 3+ devotionals viewed per session

---

#### B. Reading Experience

**Priority**: P0 (Must-Have for MVP)

**Description**: Beautiful, distraction-free reading experience optimized for mobile.

**Functional Requirements**:

1. **Content Display**
   - Clean typography (Cormorant Garamond for headings, DM Sans for body)
   - Responsive layout (mobile, tablet, desktop)
   - Hero image at top
   - Title, author, date, reading time
   - Structured content blocks:
     - Paragraphs
     - Scripture blocks (styled differently)
     - Prayer sections
     - Reflection questions
   - Smooth scroll

2. **Reading Controls**
   - **Font Size**: Toggle between Small, Medium, Large
   - **Theme**: Light mode, Dark mode (future)
   - **Line Height**: Compact, Comfortable, Spacious
   - **Audio Player**: Play/pause, speed control (0.75x, 1x, 1.25x, 1.5x), progress bar

3. **Scripture References**
   - Inline scripture references are tappable
   - Popup shows full verse text
   - "Explain" button for AI context (future)
   - Copy verse to clipboard
   - Share verse

4. **Progress Tracking**
   - Mark as read when scrolled to bottom
   - Save reading position for longer devotionals
   - "Continue reading" badge if partially read

5. **Related Content**
   - "More from this author"
   - "Related devotionals" based on category/scripture
   - "Next devotional" button

**Non-Functional Requirements**:
- Text must be readable on all screen sizes (320px+)
- No layout shift during loading
- Font size changes apply instantly

**User Interface**:
- Fixed top bar: Back button, Font size, Audio, Bookmark, Share
- Content area: Full-width on mobile, max-width 700px on desktop
- Bottom actions: Like, Comment, Share, Bookmark

**Success Metrics**:
- Average reading time > 3 minutes
- 60%+ read to end (scroll depth)
- 40%+ use audio feature

---

#### C. Discovery

**Priority**: P1 (High Priority, Post-MVP)

**Description**: Tools to discover and explore devotional content.

**Functional Requirements**:

1. **Browse by Date**
   - Calendar view showing available devotionals
   - Click date to view devotional
   - Navigate months easily

2. **Browse by Topic/Category**
   - Grid of categories (Faith, Prayer, Hope, etc.)
   - Click to see all devotionals in category
   - Category description and icon

3. **Search**
   - Search bar at top of app
   - Full-text search on:
     - Devotional title
     - Content
     - Scripture references
     - Author name
   - Auto-suggest as typing
   - Search results page with filters (date, category, author)

4. **Random Devotional**
   - "Inspire Me" button
   - Shows random devotional from catalog
   - Biased towards user's favorite categories (future)

5. **Yearly Devotional Index**
   - List/grid view of all devotionals for a year
   - Group by month
   - Quick navigation

6. **Scripture Reference Search (Future)**
   - Search by book, chapter, verse (e.g., "John 3:16")
   - Find all devotionals that reference that verse
   - Cross-reference view

**Non-Functional Requirements**:
- Search returns results in < 500ms
- Support fuzzy matching (typos)
- Index updated within 1 minute of new devotional

**User Interface**:
- Prominent search bar in header
- Filter chips (Today, This Week, This Month)
- Category grid with icons and colors

**Success Metrics**:
- 40%+ use search at least once per month
- 20%+ discover content via browse features

---

#### D. Social Interaction

**Priority**: P0 (Must-Have for MVP)

**Description**: Engage with devotionals and community through likes, comments, and shares.

**Functional Requirements**:

1. **Likes**
   - Like button on devotional and comments
   - Unlike by tapping again
   - Show total like count
   - Animate heart icon on like
   - Show list of who liked (future)

2. **Comments**
   - Add comment text (500 chars max)
   - Edit own comment (within 5 minutes)
   - Delete own comment
   - Reply to comments (threaded, max 2 levels)
   - Like comments
   - Sort by: Newest, Oldest, Most Liked
   - Paginate (20 per page)
   - "Pastor's Reply" badge for pastor comments

3. **Bookmarks/Favorites**
   - Bookmark button on devotional
   - Save to personal bookmarks collection
   - Access from profile
   - Organize with folders (future)

4. **Shares**
   - Share button with options:
     - **WhatsApp**: Share link with title and excerpt
     - **Facebook**: Share with Open Graph preview
     - **Twitter**: Share with custom text (title + link)
     - **Instagram Stories**: Export as image with quote
     - **Copy Link**: Copy shareable URL
   - Track share count per platform

5. **Community Safety**
   - Report abusive comment
   - Block user
   - Pastor can delete any comment on their devotionals
   - Moderation queue for pastor (future)

**Non-Functional Requirements**:
- Likes and comments save instantly (optimistic UI)
- Shares generate preview in < 1 second
- WhatsApp deep link works on mobile

**User Interface**:
- Action bar: Like, Comment, Bookmark, Share (icons + counts)
- Comments section below devotional content
- Reply button inline with each comment
- Share modal with platform icons

**Success Metrics**:
- 30%+ of readers engage (like/comment/share)
- WhatsApp shares > 50% of all shares (African market)
- Comments contribute to community feel (qualitative)

---

#### E. User Profile

**Priority**: P0 (Must-Have for MVP)

**Description**: Personal profile showing reading history, stats, and preferences.

**Functional Requirements**:

1. **Profile Information**
   - Profile photo
   - Display name
   - Bio (optional)
   - Joined date
   - Edit profile button

2. **Reading Stats**
   - **Devotionals Read**: Total count
   - **Day Streak**: Consecutive days reading
   - **Bookmarked**: Count of saved devotionals
   - **Liked**: Count of liked devotionals
   - **Comments**: Count of comments posted

3. **Reading History**
   - List of all read devotionals
   - Sort by: Most recent, Oldest first
   - Date read
   - Re-read indicator if read multiple times
   - Clear history button

4. **Bookmarks**
   - Grid/list of bookmarked devotionals
   - Remove from bookmarks
   - Sort by: Date bookmarked, Title
   - Search within bookmarks

5. **Preferences**
   - Notification settings
   - Reading preferences (font size, theme)
   - Email notifications
   - Language (future)

6. **Account Management**
   - Change password
   - Email preferences
   - Delete account
   - Sign out

**Non-Functional Requirements**:
- Profile loads in < 2 seconds
- History supports 1,000+ devotionals efficiently
- Sync across devices (if logged in)

**User Interface**:
- Avatar at top with stats cards below
- Tabs: History, Bookmarks, Settings
- Consistent card layout for devotionals

**Success Metrics**:
- 50%+ view profile at least monthly
- Reading streaks motivate daily engagement (qualitative)

---

## 4. AI Features

### 4.1 Phase 1: MVP AI Features

#### A. AI Text-to-Speech (TTS)

**Priority**: P0 (Must-Have for MVP)

**Description**: Convert devotional text to natural-sounding audio narration.

**Functional Requirements**:

1. **Audio Generation**
   - Generate audio when devotional is published (async)
   - Use OpenAI TTS or ElevenLabs API
   - Voice: Professional, warm, spiritual tone
   - Support multiple voices (future): Male, Female, different accents
   - Pastor can upload own voice recording instead (overrides AI)

2. **Audio Player**
   - Embedded player in devotional reading view
   - Controls: Play/Pause, Seek, Speed (0.75x, 1x, 1.25x, 1.5x, 2x)
   - Progress bar with time indicator
   - Continue where you left off (resume)
   - Download for offline (future - Pro plan)

3. **Audio Quality**
   - Bitrate: 128 kbps MP3
   - Sample rate: 44.1 kHz
   - Optimize for voice (not music)
   - File size < 5MB for 10-minute devotional

**Technical Implementation**:
- Queue audio generation as background job
- Store audio in Hetzner storage (from @shared/)
- Cache audio URLs for 1 year
- Fallback: If generation fails, show "Audio coming soon"

**Non-Functional Requirements**:
- Generation time < 1 minute for 1,000-word devotional
- Audio plays smoothly without buffering on 3G
- Player loads in < 500ms

**Success Metrics**:
- 40%+ of readers use audio at least once
- Average listen-through rate > 60%

---

#### B. AI Summary

**Priority**: P1 (High Priority, Post-MVP)

**Description**: Generate a one-paragraph summary of devotional for quick reading.

**Functional Requirements**:

1. **Summary Generation**
   - Generate summary when devotional is published (async)
   - Use GPT-4 or similar LLM
   - Prompt: "Summarize this devotional in 1 paragraph (50-75 words). Capture the main spiritual message and key takeaway."
   - Include main scripture reference if applicable
   - Preserve spiritual tone

2. **Summary Display**
   - Show summary card above full devotional
   - Collapsible: "Read Summary" / "Hide Summary"
   - Styling: Lighter background, italic text
   - "Read Full Devotional" button below summary

3. **Summary Quality**
   - Coherent, grammatically correct
   - Captures essence of message
   - Avoids generic platitudes
   - Pastor can edit or disable summary

**Technical Implementation**:
- Queue summary generation as background job
- Store summary in devotional document
- Retry 3 times if generation fails
- Fallback: Show first 100 chars of devotional as excerpt

**Non-Functional Requirements**:
- Generation time < 30 seconds
- Summary length: 50-75 words consistently
- Success rate > 95%

**Success Metrics**:
- 30%+ of readers read summary
- 20% read summary instead of full devotional (time-saving benefit)

---

#### C. AI Scripture Explanation

**Priority**: P1 (High Priority, Post-MVP)

**Description**: Provide historical context and meaning for scripture references.

**Functional Requirements**:

1. **Explanation Trigger**
   - Tap any scripture reference in devotional
   - "Explain" button in scripture popup
   - Modal appears with explanation

2. **Explanation Content**
   - **Context**: Historical background (who, when, where, why)
   - **Meaning**: What the verse means in original context
   - **Application**: How it applies today
   - Length: 100-200 words
   - Sources: Cite biblical commentary sources (future)

3. **Explanation Generation**
   - Use GPT-4 with system prompt:
     - "You are a biblical scholar. Provide a concise explanation of [verse]. Include historical context, original meaning, and modern application. Keep it accessible for general audience. Avoid denominational bias. 100-200 words."
   - Cache explanations for reused verses
   - Pastor can provide custom explanations (overrides AI)

4. **Related Features**
   - "Learn More" links to Bible study resources (future)
   - Share verse + explanation
   - Save explanation to notes (future)

**Technical Implementation**:
- Generate on-demand (when user taps)
- Cache in database with verse reference as key
- Preload common verses (John 3:16, Psalms 23:1, etc.)
- Fallback: Show verse translation notes from Bible API

**Non-Functional Requirements**:
- Explanation loads in < 2 seconds
- Cache hit rate > 80% (reuse for common verses)
- Explanations are theologically sound

**Success Metrics**:
- 25%+ of readers use explanation feature
- Users report deeper understanding (survey)

---

### 4.2 Phase 2: Advanced AI Features (Future)

#### D. AI Interactive Spiritual Assistant

**Priority**: P3 (Future Enhancement)

**Description**: Conversational AI assistant trained on pastor's devotionals to guide readers.

**Functional Requirements**:

1. **Chat Interface**
   - Chat button in app (bottom-right corner)
   - Opens chat modal
   - User can ask questions in natural language
   - AI responds in real-time (streaming)

2. **Capabilities**
   - **Recommend Devotionals**: "What should I read about hope?"
   - **Answer Spiritual Questions**: "How do I overcome anxiety?"
   - **Explain Scripture**: "What does Romans 8:28 mean?"
   - **Guide Prayer**: "Lead me in a prayer for my family"
   - **Reflect Together**: "I'm struggling with forgiveness. Can you help?"

3. **Training & Knowledge**
   - Fine-tuned on all pastor's devotionals
   - Trained on selected biblical texts
   - Includes pastor's tone and theology
   - Pastor sets boundaries:
     - Approved topics
     - Theological positions
     - Restricted topics (AI won't answer)

4. **Pastor Control Panel**
   - Enable/disable assistant
   - Review conversation logs (anonymized)
   - Edit AI's knowledge base
   - Set response guidelines
   - Flagged conversations for review

5. **Safety & Ethics**
   - Refuses harmful requests
   - Avoids medical/legal/financial advice
   - Refers to pastor or professional when appropriate
   - Transparent: "I'm an AI, not a replacement for pastoral care"
   - Privacy: Conversations are private, not shared

**Technical Implementation**:
- Use GPT-4 with RAG (Retrieval Augmented Generation)
- Vector database of devotional embeddings
- System prompt includes pastor's values and guidelines
- Streaming response for better UX
- Rate limiting to control costs

**Non-Functional Requirements**:
- Response time < 3 seconds
- Conversation history saved per user
- Support 100+ concurrent conversations
- Cost < $0.10 per conversation

**Success Metrics**:
- 20%+ of readers use assistant
- Positive feedback score > 4/5
- Users report feeling spiritually supported

---

## 5. Technical Requirements

### 5.1 Performance

| Metric | Target |
|--------|--------|
| **Page Load Time** | < 2 seconds (First Contentful Paint) |
| **Time to Interactive** | < 3 seconds |
| **Largest Contentful Paint** | < 2.5 seconds |
| **Cumulative Layout Shift** | < 0.1 |
| **First Input Delay** | < 100ms |
| **API Response Time** | < 500ms (p95) |
| **Database Query Time** | < 100ms (p95) |
| **Audio Playback** | No buffering on 3G (3 Mbps) |
| **Image Load** | Lazy-load, < 1 second per image |
| **Offline Support** | Cache previously loaded devotionals (PWA) |

### 5.2 Database (MongoDB)

**Database Name**: `devotionalflow`

**Collections & Schemas**:

#### 1. Users Collection

```javascript
{
  _id: ObjectId,
  email: String (unique, indexed),
  password_hash: String,
  name: String,
  role: Enum["pastor", "reader"],
  avatar_url: String,
  bio: String,
  // Pastor-specific fields
  ministry_name: String,
  ministry_website: String,
  subscription_plan: Enum["free", "pro", "ministry"],
  subscription_expires_at: Date,
  // Reader-specific fields
  reading_streak: Number,
  reading_preferences: {
    font_size: Enum["small", "medium", "large"],
    theme: Enum["light", "dark"],
    notification_time: String // "08:00", "12:00", "20:00"
  },
  created_at: Date,
  updated_at: Date
}
```

**Indexes**:
- `email` (unique)
- `role`
- `created_at`

---

#### 2. Devotionals Collection

```javascript
{
  _id: ObjectId,
  author_id: ObjectId (ref: Users, indexed),
  title: String (indexed, text search),
  slug: String (unique, indexed), // URL-friendly: "finding-hope-in-difficult-times"
  content: Array[ // Structured blocks
    {
      type: Enum["paragraph", "scripture", "prayer", "reflection"],
      text: String,
      scripture_reference: String // e.g., "John 3:16" (only for scripture type)
    }
  ],
  excerpt: String, // First 150 chars
  scripture_references: Array[String], // All referenced verses
  categories: Array[String], // ["faith", "hope", "prayer"]
  status: Enum["draft", "scheduled", "published"],
  scheduled_at: Date,
  published_at: Date,
  // Media
  cover_image_url: String,
  audio_url: String, // AI-generated or uploaded
  video_url: String,
  // AI-generated content
  summary: String, // AI summary
  // Engagement metrics
  views_count: Number (default: 0),
  likes_count: Number (default: 0),
  comments_count: Number (default: 0),
  shares_count: Number (default: 0),
  bookmarks_count: Number (default: 0),
  // Metadata
  reading_time_minutes: Number, // Estimated
  created_at: Date,
  updated_at: Date
}
```

**Indexes**:
- `author_id`
- `slug` (unique)
- `status`
- `published_at`
- `categories`
- `title` (text search)
- `content.text` (text search)

---

#### 3. Comments Collection

```javascript
{
  _id: ObjectId,
  devotional_id: ObjectId (ref: Devotionals, indexed),
  user_id: ObjectId (ref: Users, indexed),
  parent_comment_id: ObjectId (ref: Comments, indexed, nullable), // For threaded replies
  text: String (max 500 chars),
  likes_count: Number (default: 0),
  is_pastor_reply: Boolean, // True if author of devotional replied
  created_at: Date,
  updated_at: Date,
  deleted_at: Date // Soft delete
}
```

**Indexes**:
- `devotional_id`
- `user_id`
- `parent_comment_id`
- `created_at`

---

#### 4. Likes Collection

```javascript
{
  _id: ObjectId,
  user_id: ObjectId (ref: Users, indexed),
  target_type: Enum["devotional", "comment"],
  target_id: ObjectId (indexed), // Devotional or Comment ID
  created_at: Date
}
```

**Indexes**:
- `(user_id, target_type, target_id)` (unique compound)
- `target_id`

---

#### 5. Bookmarks Collection

```javascript
{
  _id: ObjectId,
  user_id: ObjectId (ref: Users, indexed),
  devotional_id: ObjectId (ref: Devotionals, indexed),
  created_at: Date
}
```

**Indexes**:
- `(user_id, devotional_id)` (unique compound)
- `devotional_id`

---

#### 6. ReadingHistory Collection

```javascript
{
  _id: ObjectId,
  user_id: ObjectId (ref: Users, indexed),
  devotional_id: ObjectId (ref: Devotionals, indexed),
  read_at: Date,
  reading_progress: Number (0-100), // Scroll percentage
  listening_progress: Number (0-100) // Audio progress
}
```

**Indexes**:
- `user_id`
- `devotional_id`
- `read_at`
- `(user_id, devotional_id)` (compound for upsert)

---

#### 7. Follows Collection (Future - Multi-Pastor)

```javascript
{
  _id: ObjectId,
  follower_id: ObjectId (ref: Users, indexed),
  following_id: ObjectId (ref: Users, indexed),
  created_at: Date
}
```

**Indexes**:
- `(follower_id, following_id)` (unique compound)
- `following_id`

---

### 5.3 RESTful API Endpoints

**Base URL**: `https://devotionalflow-api.ailabsafrica.com/api/v1`

**Authentication**: All endpoints require JWT token in `Authorization: Bearer <token>` header (except auth routes).

#### Authentication Routes

```
POST   /auth/signup              # Register new user
POST   /auth/login               # Login (returns JWT)
POST   /auth/logout              # Logout (blacklist token)
GET    /auth/me                  # Get current user
POST   /auth/refresh             # Refresh JWT token
POST   /auth/forgot-password     # Request password reset
POST   /auth/reset-password      # Reset password with token
```

#### Devotional Routes

```
POST   /devotionals              # Create new devotional
GET    /devotionals              # List devotionals (with filters, pagination)
GET    /devotionals/:id          # Get single devotional
PUT    /devotionals/:id          # Update devotional
DELETE /devotionals/:id          # Delete devotional
POST   /devotionals/:id/publish  # Publish devotional
POST   /devotionals/:id/schedule # Schedule devotional
GET    /devotionals/:id/analytics # Get devotional analytics
```

#### User Routes

```
GET    /users/:id                # Get user profile
PUT    /users/:id                # Update user profile
GET    /users/:id/devotionals    # Get user's devotionals
GET    /users/:id/bookmarks      # Get bookmarked devotionals
GET    /users/:id/history        # Get reading history
POST   /users/:id/follow         # Follow/unfollow user
GET    /users/:id/followers      # Get followers
GET    /users/:id/following      # Get following
```

#### Comment Routes

```
GET    /devotionals/:id/comments # Get comments for devotional
POST   /devotionals/:id/comments # Add comment
PUT    /comments/:id             # Update comment
DELETE /comments/:id             # Delete comment
POST   /comments/:id/like        # Like/unlike comment
```

#### Engagement Routes

```
POST   /devotionals/:id/like     # Like/unlike devotional
POST   /devotionals/:id/bookmark # Bookmark/unbookmark
POST   /devotionals/:id/view     # Track view
POST   /devotionals/:id/share    # Track share (with platform)
```

#### Analytics Routes

```
GET    /analytics/dashboard      # Dashboard stats (pastor)
GET    /analytics/devotional/:id # Devotional-specific analytics
GET    /analytics/engagement     # Engagement trends
GET    /analytics/readers        # Reader insights
```

#### AI Routes

```
POST   /ai/tts                   # Generate text-to-speech
POST   /ai/summary               # Generate summary
POST   /ai/scripture-explain     # Explain scripture
POST   /ai/assist                # AI writing assistance (pastor)
POST   /ai/chat                  # AI spiritual assistant (future)
```

#### Media Routes

```
POST   /media/upload             # Upload image/audio/video
GET    /media/:id                # Get media file
DELETE /media/:id                # Delete media file
```

#### Search Routes

```
GET    /search/devotionals       # Search devotionals
GET    /search/scriptures        # Search by scripture reference
GET    /search/users             # Search pastors
```

---

### 5.4 File Storage (Hetzner Storage from @shared/)

**Note**: DevotionalFlow uses **Hetzner Storage** as configured in `@shared/`, not S3.

**Storage Structure**:

```
hetzner-storage/
├── devotionalflow/
│   ├── images/
│   │   ├── covers/           # Devotional cover images
│   │   │   └── {devotional_id}_{timestamp}.jpg
│   │   ├── inline/           # Inline content images
│   │   │   └── {devotional_id}_{timestamp}.jpg
│   │   └── avatars/          # User profile photos
│   │       └── {user_id}_{timestamp}.jpg
│   │
│   ├── audio/
│   │   ├── generated/        # AI-generated TTS audio
│   │   │   └── {devotional_id}_tts.mp3
│   │   └── uploaded/         # Pastor-uploaded audio
│   │       └── {devotional_id}_{timestamp}.mp3
│   │
│   └── video/                # Optional video content
│       └── {devotional_id}_{timestamp}.mp4
```

**Upload Requirements**:
- **Images**:
  - Formats: JPEG, PNG, WebP
  - Max size: 5MB
  - Resize to max 1920x1080
  - Generate thumbnails (400x225)
- **Audio**:
  - Formats: MP3, M4A, WAV
  - Max size: 20MB
  - Convert to 128 kbps MP3
- **Video** (Future):
  - Formats: MP4, MOV
  - Max size: 50MB
  - Transcode to 720p MP4

**CDN**:
- Serve media via Hetzner CDN
- Cache: 1 year for images/audio, 1 week for avatars
- Compression: Gzip for text, optimize images

---

### 5.5 AI Integration

#### OpenAI (Text-to-Speech & LLM)

```python
# TTS
from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

response = client.audio.speech.create(
    model="tts-1",
    voice="alloy",  # Options: alloy, echo, fable, onyx, nova, shimmer
    input=devotional_content
)

# Summary Generation
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a spiritual writer. Summarize devotionals concisely."},
        {"role": "user", "content": f"Summarize this devotional in 1 paragraph:\n\n{content}"}
    ]
)
```

#### Scripture API

Use **Bible API** (https://scripture.api.bible/) or **ESV API** for verse lookup:

```python
import requests

def fetch_verse(reference: str, translation: str = "KJV"):
    # Example: "John 3:16", "KJV"
    response = requests.get(
        f"https://api.scripture.api.bible/v1/bibles/{translation}/passages/{reference}",
        headers={"Authorization": f"Bearer {BIBLE_API_KEY}"}
    )
    return response.json()["content"]
```

---

### 5.6 Security

1. **Authentication**:
   - Supabase for OAuth and JWT
   - Password hashing: bcrypt with 12 rounds
   - JWT expiry: 1 hour (refresh token: 30 days)

2. **Authorization**:
   - Role-based access control (RBAC)
   - Pastor can only edit their own devotionals
   - Admin role for multi-pastor organizations

3. **API Security**:
   - Rate limiting: 100 requests/minute per IP
   - CORS: Allow only production domains
   - Input validation: Pydantic models
   - SQL/NoSQL injection prevention

4. **Data Privacy**:
   - GDPR compliance: Data export, deletion, consent
   - Encrypt sensitive data at rest
   - HTTPS/TLS everywhere

5. **Content Moderation**:
   - Report system for abusive content
   - Pastor review queue
   - Auto-flag system (profanity, spam)

---

### 5.7 SEO Optimization

1. **Meta Tags**:
   - Dynamic `<title>`, `<meta description>`, `<meta keywords>` per devotional
   - Open Graph tags for social sharing
   - Twitter Card tags

2. **Structured Data**:
   - Schema.org `Article` markup for devotionals
   - `Person` markup for pastor profiles
   - Breadcrumbs

3. **Performance**:
   - Server-side rendering (SSR) for public pages
   - Preload critical resources
   - Optimize images (WebP, lazy-load)

4. **Sitemap**:
   - Auto-generate sitemap.xml
   - Submit to Google Search Console

---

## 6. Design Requirements

### 6.1 Brand Identity

**Mission**: Inspire, uplift, and connect through beautiful spiritual design.

**Design Principles**:
1. **Calm**: Generous white space, soft colors, minimal distractions
2. **Elegant**: Sophisticated typography, refined layouts
3. **Spiritual**: Colors and imagery evoke faith, hope, peace
4. **Accessible**: Readable for all ages, high contrast, responsive

---

### 6.2 Color Palette

| Color Name | Hex Code | RGB | Usage |
|------------|----------|-----|-------|
| **Deep Navy** | `#1a2332` | `26, 35, 50` | Primary backgrounds, headers, trust & depth |
| **Soft Gold** | `#d4a650` | `212, 166, 80` | Accents, CTAs, divine light & warmth |
| **Teal** | `#2d7c7c` | `45, 124, 124` | Secondary accents, hope & renewal |
| **Cream** | `#f8f6f3` | `248, 246, 243` | Backgrounds, cards, peace & cleanliness |
| **Charcoal** | `#2d3748` | `45, 55, 72` | Body text, high contrast |
| **Soft Gray** | `#718096` | `113, 128, 150` | Secondary text, borders |
| **Pure White** | `#ffffff` | `255, 255, 255` | Backgrounds, content areas |

**Gradients**:
- **Sunrise Gradient**: `linear-gradient(135deg, #d4a650 0%, #2d7c7c 100%)`
- **Evening Gradient**: `linear-gradient(135deg, #1a2332 0%, #2d7c7c 100%)`

---

### 6.3 Typography

**Font Families**:

1. **Headings & Titles**: [Cormorant Garamond](https://fonts.google.com/specimen/Cormorant+Garamond)
   - Weights: 400 (Regular), 600 (Semi-Bold), 700 (Bold)
   - Serif font with elegant, spiritual feel
   - Use for: H1, H2, H3, devotional titles

2. **Body Text**: [DM Sans](https://fonts.google.com/specimen/DM+Sans)
   - Weights: 400 (Regular), 500 (Medium), 700 (Bold)
   - Sans-serif font, modern and highly readable
   - Use for: Paragraphs, buttons, labels, UI text

**Type Scale**:

| Element | Font | Size | Weight | Line Height |
|---------|------|------|--------|-------------|
| **H1** | Cormorant | 48px (3rem) | 700 | 1.2 |
| **H2** | Cormorant | 36px (2.25rem) | 600 | 1.3 |
| **H3** | Cormorant | 28px (1.75rem) | 600 | 1.4 |
| **H4** | DM Sans | 24px (1.5rem) | 700 | 1.4 |
| **Body** | DM Sans | 16px (1rem) | 400 | 1.75 |
| **Small** | DM Sans | 14px (0.875rem) | 400 | 1.5 |
| **Caption** | DM Sans | 12px (0.75rem) | 500 | 1.4 |

---

### 6.4 Visual Style

**Spacing**:
- Base unit: 4px
- Scale: 4, 8, 12, 16, 24, 32, 48, 64, 96, 128px

**Shadows**:
- **Card**: `0 2px 8px rgba(0, 0, 0, 0.08)`
- **Elevated**: `0 4px 16px rgba(0, 0, 0, 0.12)`
- **Modal**: `0 8px 32px rgba(0, 0, 0, 0.16)`

**Border Radius**:
- Small: 4px (buttons, inputs)
- Medium: 8px (cards)
- Large: 16px (modals, images)
- Full: 9999px (avatars, pills)

**Animations**:
- **Duration**: 200ms (fast), 300ms (normal), 500ms (slow)
- **Easing**: `cubic-bezier(0.4, 0, 0.2, 1)` (smooth)
- **Effects**:
  - Fade in/out
  - Slide up/down
  - Float (gentle up-down motion)
  - Glow (subtle pulse)

---

### 6.5 Component Guidelines

**Buttons**:
- Primary: Soft Gold background, white text, shadow on hover
- Secondary: Outlined, transparent background, gold border
- Ghost: No background, underline on hover

**Cards**:
- White background with subtle shadow
- 8px border radius
- 16px padding
- Hover effect: Slight lift (shadow increase)

**Inputs**:
- Bordered, rounded corners
- Focus: Gold ring
- Error: Red border + error message below

**Icons**:
- Use [Lucide React](https://lucide.dev/) for consistency
- Size: 16px (small), 20px (normal), 24px (large)
- Color: Inherit from parent or use gray/gold

---

## 7. Subscription Model

### 7.1 Pricing Tiers

#### Free Plan (Pastor)

**Price**: $0/month

**Features**:
- ✅ Up to 10 devotionals
- ✅ Basic text editor
- ✅ Basic analytics (views, likes, comments count)
- ✅ Up to 100 readers
- ✅ Community support
- ❌ No AI TTS
- ❌ No scheduling
- ❌ No custom branding

**Target Audience**:
- New pastors testing the platform
- Small churches with limited budgets
- Personal devotional writers

---

#### Pro Plan (Pastor)

**Price**: $12/month or $120/year (save $24)

**Features**:
- ✅ Unlimited devotionals
- ✅ Full analytics dashboard (trends, demographics, engagement)
- ✅ Unlimited readers
- ✅ **AI Text-to-Speech** for all devotionals
- ✅ **AI Summary** generation
- ✅ **AI Scripture Explanation**
- ✅ Custom branding (logo, colors)
- ✅ Social sharing templates (Instagram, Facebook)
- ✅ Push notifications to readers
- ✅ Calendar scheduling
- ✅ Priority email support
- ✅ Export analytics (CSV)

**Target Audience**:
- Active pastors with growing congregations
- Digital-first ministries
- Pastors seeking professional tools

---

#### Ministry Plan (Pastor)

**Price**: $29/month or $290/year (save $58)

**Features**:
- ✅ Everything in Pro
- ✅ **Multi-pastor support** (up to 5 pastors)
- ✅ Role management (admin, editor, contributor)
- ✅ Content approval workflow
- ✅ **API access** for integrations
- ✅ **Custom domain** (e.g., devotions.yourchurch.com)
- ✅ White-label option (remove DevotionalFlow branding)
- ✅ Priority phone support
- ✅ Advanced analytics (geographic heatmap, cohort analysis)
- ✅ Bulk import devotionals

**Target Audience**:
- Multi-site churches
- Large ministries (1,000+ members)
- Organizations with multiple pastors

---

### 7.2 Reader Monetization (Future)

**Reader Access**: Completely free for all features.

**Optional "Support the Ministry" Feature**:
- Readers can voluntarily subscribe ($3-10/month, user-chosen amount)
- Revenue goes directly to pastor (DevotionalFlow takes 10% platform fee)
- Benefits for supporters:
  - Special "Supporter" badge in comments
  - Early access to devotionals (pastor can enable)
  - Exclusive content (pastor can create)
- Powered by Mobile Money (MoMo), Stripe, PayPal

---

## 8. Success Metrics

### 8.1 Pastor KPIs

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Devotionals Published/Month** | 15+ per pastor | Track via database |
| **Daily Active Creators** | 60% of pastors publish at least 3x/week | Login frequency + publish events |
| **Paid Account Retention** | 85% annual retention | Subscription renewals |
| **Engagement Rate** | 25%+ (likes/comments per 100 readers) | Engagement count / views * 100 |

### 8.2 Reader KPIs

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Daily Active Readers** | 40% of registered readers read daily | Login + read events |
| **Average Time Spent Reading** | 4+ minutes per devotional | Reading time tracking |
| **Audio Listen Rate** | 35%+ use audio at least once | Audio play events |
| **WhatsApp Share Rate** | 20%+ share to WhatsApp | Share tracking (platform: WhatsApp) |
| **7-Day Returning User %** | 60%+ return within 7 days | Cohort analysis |
| **30-Day Returning User %** | 40%+ return within 30 days | Cohort analysis |

### 8.3 Business KPIs

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Monthly Recurring Revenue (MRR)** | $10,000 by Month 6 | Subscription revenue |
| **Customer Acquisition Cost (CAC)** | < $20 per pastor | Marketing spend / new signups |
| **Lifetime Value (LTV)** | > $200 per pastor | Average revenue per pastor over 18 months |
| **Churn Rate** | < 10% monthly | Cancellations / active subscriptions |
| **Free-to-Paid Conversion** | 15%+ within 30 days | Free users upgrading to Pro |

---

## 9. Implementation Roadmap

### Phase 1: MVP Backend Foundation (6-8 weeks)

**Goal**: Functional backend with authentication, devotional CRUD, and basic engagement.

**Week 1-2: Foundation**
- ✅ FastAPI application structure
- ✅ MongoDB connection and schemas
- ✅ Supabase authentication integration
- ✅ User CRUD (create, read, update, delete)
- ✅ Basic unit tests setup

**Week 3-4: Devotional System**
- ✅ Devotional CRUD with draft/published/scheduled states
- ✅ File upload for images (Hetzner storage)
- ✅ Devotional listing with pagination and filters
- ✅ Slug generation for SEO-friendly URLs

**Week 5-6: Engagement Features**
- ✅ Comments system (create, read, delete, threaded replies)
- ✅ Likes and bookmarks
- ✅ Reading history tracking
- ✅ View count tracking

**Week 7-8: Integration & Testing**
- ✅ Frontend integration (replace mock data)
- ✅ Basic analytics APIs (dashboard stats)
- ✅ Comprehensive unit tests for all CRUD
- ✅ Integration tests with real database
- ✅ Deployment setup (Nginx, systemd, SSL)

**Success Criteria**:
- Pastors can create, edit, publish devotionals
- Readers can view, like, comment, bookmark
- Authentication works end-to-end
- All tests passing (80%+ coverage)

---

### Phase 2: Core Features (4-6 weeks)

**Goal**: Add AI features, search, notifications, and advanced analytics.

**Week 1-2: AI Integration**
- ✅ OpenAI TTS integration for audio generation
- ✅ Scripture API integration
- ✅ Audio player enhancements (resume, speed control)
- ✅ Hetzner storage for audio files

**Week 3-4: Search & Discovery**
- ✅ Full-text search on devotionals (MongoDB text index)
- ✅ Search by scripture reference
- ✅ Category browsing
- ✅ Calendar view API

**Week 5-6: Notifications & Analytics**
- ✅ Push notification system (Firebase)
- ✅ Email notifications (SMTP/SendGrid)
- ✅ Advanced analytics dashboard
- ✅ Engagement trends and charts API

**Success Criteria**:
- AI audio works for all devotionals
- Search returns relevant results
- Notifications delivered reliably
- Analytics provide actionable insights

---

### Phase 3: AI Enhancement (4-6 weeks)

**Goal**: Advanced AI features and personalization.

**Week 1-2: AI Content Generation**
- ✅ AI summary generation
- ✅ AI scripture explanations
- ✅ Pastor writing assistance

**Week 3-4: Recommendation Engine**
- ✅ Personalized devotional recommendations
- ✅ "Because you read..." section
- ✅ Reading streak tracking

**Week 5-6: Social Features**
- ✅ Social sharing templates (Instagram, WhatsApp)
- ✅ Share tracking by platform
- ✅ Enhanced comment features (pinning, best comments)

**Success Criteria**:
- AI summaries are helpful and accurate
- Recommendations increase engagement
- Social shares drive new readers

---

### Phase 4: Advanced Features (6-8 weeks)

**Goal**: Scale platform with multi-pastor, monetization, and mobile apps.

**Week 1-2: Multi-Pastor Support**
- ✅ Organization accounts
- ✅ Team roles (admin, editor, contributor)
- ✅ Content approval workflow

**Week 3-4: Monetization**
- ✅ Mobile Money (MoMo) integration
- ✅ Stripe and PayPal integration
- ✅ "Support the Ministry" feature
- ✅ Revenue dashboard for pastors

**Week 5-6: AI Spiritual Assistant**
- ✅ Conversational AI chatbot
- ✅ RAG with pastor's devotionals
- ✅ Pastor control panel for AI

**Week 7-8: Mobile Apps**
- ✅ React Native app for iOS and Android
- ✅ Push notifications
- ✅ Offline reading
- ✅ App store submission

**Success Criteria**:
- Multi-pastor organizations onboarded
- Donations flowing to pastors
- AI assistant provides value
- Mobile apps downloaded and active

---

## 10. User Stories

### Pastor Stories

1. **As a pastor, I want to schedule devotionals for the entire month so I can focus on ministry work without daily publishing tasks.**
   - Acceptance Criteria: Can select future date, devotional publishes automatically, calendar shows scheduled posts

2. **As a pastor, I want to see engagement stats to understand what my audience connects with most.**
   - Acceptance Criteria: Dashboard shows views, likes, comments per devotional, trends over time, top-performing content

3. **As a pastor, I want a simple, beautiful writing space that inspires me and doesn't distract from the message.**
   - Acceptance Criteria: Clean editor, autosave, scripture lookup, no clutter, responsive on mobile

4. **As a pastor, I want to upload audio recordings of my voice reading devotionals so my congregation can hear my personal delivery.**
   - Acceptance Criteria: Upload MP3, audio replaces AI TTS, audio player works, file size < 20MB

5. **As a pastor, I want to respond to comments and build relationships with readers beyond Sunday services.**
   - Acceptance Criteria: Can reply to comments, replies marked "Pastor's Reply", notifications sent to commenter

### Reader Stories

1. **As a reader, I want to listen to today's devotional while commuting so I can stay spiritually fed despite my busy schedule.**
   - Acceptance Criteria: Audio available for all devotionals, player has play/pause/speed controls, works offline

2. **As a reader, I want to comment and share thoughts with others so I feel part of a spiritual community.**
   - Acceptance Criteria: Can add comments, see others' comments, like comments, reply to comments

3. **As a reader, I want to explore past devotionals easily so I can revisit messages that spoke to me.**
   - Acceptance Criteria: Browse by date, search by keyword, bookmark favorites, reading history saved

4. **As a reader, I want to share devotionals on WhatsApp with my family group so we can discuss together.**
   - Acceptance Criteria: Share button opens WhatsApp, link preview shows title + excerpt + image, works on mobile

5. **As a reader, I want to track my reading streak so I stay motivated to read daily.**
   - Acceptance Criteria: Streak count shown in profile, notification if streak at risk, achievements for milestones

---

## 11. Risks & Mitigations

### 11.1 Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **AI TTS costs spiral** | High | Medium | Usage limits on free tier, cache audio, optimize prompts, consider cheaper TTS providers |
| **Database scaling issues** | High | Low | Proper indexing, pagination, implement caching (Redis), MongoDB sharding if needed |
| **File storage costs** | Medium | Medium | Hetzner storage is cost-effective, implement CDN, compression, size limits, lifecycle policies |
| **Audio generation delays** | Medium | Medium | Async background jobs, queue system, show "Audio coming soon" fallback |
| **Scripture API rate limits** | Low | Medium | Cache common verses, implement own Bible database, use multiple API providers |

---

### 11.2 Business Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Low pastor adoption** | High | Medium | Focus on African market first, partner with churches, word-of-mouth, free trial for Pro plan |
| **Reader engagement drop-off** | High | Medium | Push notifications, streak tracking, community features, personalized recommendations |
| **Competition from free platforms** | Medium | High | Emphasize unique AI features, beautiful UX, mobile-first, better analytics |
| **Monetization resistance** | Medium | Medium | Generous free tier, clear ROI for pastors, affordable pricing for African market |
| **Content quality issues** | Low | Low | Pastor verification, content moderation tools, community reporting |

---

### 11.3 User Experience Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Complex pastor onboarding** | High | Medium | Guided tutorial, sample devotionals, video walkthrough, onboarding checklist |
| **Mobile performance issues** | High | Low | Optimize for mobile-first, lazy loading, image compression, PWA |
| **Notification fatigue** | Medium | Medium | User controls frequency, intelligent timing, valuable content only |
| **Comment toxicity** | Medium | Low | Report system, pastor moderation, auto-flagging, community guidelines |

---

## 12. Dependencies

### 12.1 External Services

| Service | Purpose | Critical? | Backup Plan |
|---------|---------|-----------|-------------|
| **Supabase** | Authentication | Yes | Can migrate to Auth0 or custom JWT |
| **MongoDB** | Database | Yes | Self-hosted MongoDB (current setup) |
| **Hetzner Storage** | File storage | Yes | Already using from @shared/, migrate to S3 if needed |
| **OpenAI** | TTS, LLM | Medium | ElevenLabs for TTS, other LLMs (Anthropic, Google) |
| **Bible API** | Scripture verses | Medium | Implement own Bible database, use multiple APIs |
| **Firebase** | Push notifications | Low | OneSignal, Pusher, custom solution |
| **SendGrid/SMTP** | Email | Low | Any email provider, self-hosted SMTP |

---

### 12.2 Internal Dependencies

| Service | Location | Purpose |
|---------|----------|---------|
| **Hetzner Storage** | `@shared/` | File storage for images, audio, video |
| **Shared Auth** | `@shared/auth/` | Supabase authentication utilities |
| **TTS Service (optional)** | `@apps/vapi_service/` | Existing TTS service could be leveraged |

---

## 13. Appendix

### 13.1 Glossary

- **Devotional**: A short spiritual message or reflection, typically 300-1,000 words, focused on a scripture or theme
- **Pastor**: Content creator who publishes devotionals (also called "minister" or "spiritual leader")
- **Reader**: User who consumes devotional content
- **Engagement**: Interactions with devotionals (likes, comments, shares, bookmarks)
- **Streak**: Number of consecutive days a reader has read a devotional
- **TTS**: Text-to-Speech, AI-generated audio narration
- **RAG**: Retrieval Augmented Generation, AI technique using external knowledge base

---

### 13.2 References

- **Figma Design**: [Link to design mockups] (if available)
- **Infrastructure Guide**: `/opt/kasaai/CLAUDE.md`
- **Test Suite Analysis**: `/opt/kasaai/apps/core_backend/TEST_SUITE_ANALYSIS.md`
- **Supabase Docs**: https://supabase.com/docs
- **OpenAI TTS Docs**: https://platform.openai.com/docs/guides/text-to-speech
- **Bible API Docs**: https://scripture.api.bible/

---

**Document Prepared By**: AI Labs Africa
**Contact**: admin@ailabsafrica.com
**Last Reviewed**: December 9, 2025
**Next Review**: After MVP launch

---

**End of PRD**
