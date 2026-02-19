# Module 4: Vertical Applications - Part 1

**Topics Covered:** studyflow, eventflow, churchflow

**Part of:** KasaAI Developer Intern Onboarding Course

---

## 5. Vertical Applications

### 5.1 StudyFlow (EduMate) (`@studyflow/`)

**🎯 Purpose**: AI-powered personal tutoring platform for African schools

**👥 Target Users**:
- Students (Grades 9-12)
- Parents (progress tracking, payment)
- Teachers (curriculum upload, class monitoring)
- Schools (bulk enrollment)

**✨ Key Features**:
- RAG-powered Q&A from school materials
- Voice and text conversational learning
- Practice exercises with instant feedback
- Multi-language support (English, Twi, French)
- Parent dashboard with AI progress reports
- Gamification (stars, badges, streaks)

**💰 Pricing**:
- Free Trial: 30 minutes
- Pay-as-you-learn: ₵20 = 100 minutes
- Monthly Plan: ₵50/month unlimited
- School Plan: ₵30/student/month (min 50 students)

**🔧 Shared Services Used**:
- RAG Service (Q&A from materials)
- Document Processor (PDF/DOCX processing)
- Wallet Service (pay-per-use)
- Usage Calculator (cost tracking)

**📊 Status**: Planning complete, ready for development

📖 **Read More**: `/opt/kasaai/apps/studyflow/PLANNING.md`

---

### 5.2 EventFlow (EventPilot) (`@eventflow/`)

**🎯 Purpose**: Mobile-first, AI-driven event management with automated voice follow-ups

**👥 Target Users**:
- Event Organizers (conferences, weddings, concerts)
- Transport Coordinators (logistics)
- Responsible Persons (task assignments)
- Vendors/Service Providers

**✨ Key Features**:
- Event setup wizard (auto-generates tasks)
- AI-powered task and timeline management
- **Automated voice calls** to follow up with team members
- Interactive Voice Response (IVR) for confirmations
- SMS/WhatsApp/Email reminders via n8n
- Real-time escalation for overdue tasks
- AI recommendations and risk detection

**💰 Pricing**:

| Action | Free | Basic | Premium |
|--------|------|-------|---------|
| Event creation | Free | Free | Free |
| Voice call/min | N/A | ₵2.00 | ₵1.50 |
| SMS reminder | N/A | ₵0.20 | ₵0.15 |
| WhatsApp msg | N/A | ₵0.30 | ₵0.25 |

**🔧 Shared Services Used**:
- VAPI Service (automated calls, IVR)
- n8n Workflow Service (multi-channel notifications)
- Wallet Service (pay-per-use)
- RAG Service (AI recommendations)

**📊 Status**: Concept complete, ready for development

📖 **Read More**: `/opt/kasaai/apps/eventflow/PLANNING.md`

---

### 5.3 ChurchFlow (`@churchflow/`)

**🎯 Purpose**: Church management and event coordination platform

**👥 Target Users**:
- Church Members (event registration, bus coordination)
- Transport Coordinators (route management)
- Conference Organizers (event creation)
- Church Admins (oversight, analytics)

**✨ Key Features**:
- Phone OTP authentication
- **Bus transportation coordination** with capacity tracking
- Real-time delay notifications (SMS, Push, WhatsApp, Email)
- Conference registration with digital check-in
- QR code generation and scanning (<20s check-in)
- Multi-channel notifications via n8n
- AI Voice Kiosk "Ama" with motion detection (Phase 2)
- Volunteer role management

**🚀 Deployment**:
- Port: 30030
- URL: https://churchflow.ailabsafrica.com (Prod)
- URL: https://dev-churchflow.ailabsafrica.com (Dev)

**📊 Status**: Phase 1 MVP 90% complete
- ✅ Authentication & user profiles
- ✅ Bus transportation coordination
- ✅ Conference registration & QR check-in
- ✅ Admin dashboard (fully functional)
- ⏳ Multi-channel notifications (n8n pending)
- ⏳ Mobile app (React Native - not started)

📖 **Read More**: `/opt/kasaai/apps/churchflow/PLANNING.md`, `PRD.md`, `MVP_SUMMARY.md`

---
