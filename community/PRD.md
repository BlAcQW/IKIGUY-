# African Language Community Platform - Product Requirements Document (PRD)

**Version:** 2.0
**Last Updated:** 2025-10-22
**Status:** North Star Document

---

## Executive Summary

The **African Language Community Platform** is a comprehensive MLOps-enabled dataset and model management system for African languages. It combines community-driven data collection with industry-standard ML pipeline tracking, semantic versioning, and authenticated resource distribution via Hetzner Storage Box integration.

### Mission
Build the world's largest, highest-quality, community-driven repository of African language data while preserving linguistic diversity, enabling ML research, and tracking end-to-end model development pipelines.

### Core Vision
Transform from a data collection platform into a full **MLOps ecosystem** where users can:
- Discover all resources (datasets, models, notebooks) for any African language
- Track ML training pipelines from data acquisition to deployment
- Contribute community data with quality validation
- Download versioned datasets and models with authentication
- Collaborate in real-time through language family communities

---

## Product Architecture

### System Overview
```
┌─────────────────────────────────────────────────────────────────┐
│              AFRICAN LANGUAGE MLOPS PLATFORM                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   COMMUNITY     │    │    ML/DATA      │    │   DISCOVERY     │
│   FEATURES      │    │   SCIENTISTS    │    │   & SEARCH      │
│                 │    │                 │    │                 │
│ • Submit Data   │    │ • Download      │    │ • Find Models   │
│ • Validate      │    │ • Track Runs    │    │ • Find Datasets │
│ • Collaborate   │    │ • Version       │    │ • Find Notebooks│
│ • Gamification  │    │ • Deploy        │    │ • Browse by     │
│                 │    │                 │    │   Language      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                               │
                    ┌─────────▼─────────┐
                    │   FASTAPI BACKEND │
                    │                   │
                    │ • Auth (Supabase) │
                    │ • Language Mgmt   │
                    │ • Quality System  │
                    │ • Pipeline Track  │
                    │ • Versioning      │
                    │ • File Management │
                    └─────────┬─────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   MONGODB   │    │   HETZNER   │    │   SUPABASE  │
│             │    │ STORAGE BOX │    │             │
│ • Metadata  │    │             │    │ • Auth      │
│ • Language  │    │ • Datasets  │    │ • Users     │
│ • Models    │    │ • Models    │    │ • Profiles  │
│ • Pipelines │    │ • Notebooks │    │             │
│ • Versions  │    │ • Artifacts │    │             │
└─────────────┘    └─────────────┘    └─────────────┘
```

### Technology Stack

**Backend:**
- FastAPI (Python 3.10+)
- MongoDB (metadata storage)
- Motor (async MongoDB driver)
- Pydantic v2 (data validation)
- Hetzner Storage Box (SFTP/WebDAV file storage)
- Supabase (authentication)
- Redis (caching, WebSocket)

**Frontend:**
- React 18 with TypeScript
- Vite (build tool)
- TanStack React Query (data fetching)
- shadcn/ui (component library)
- TailwindCSS (styling)
- WebSocket (real-time updates)

---

## Core Components

### 1. Resource Management System

#### 1.1 ML Model Registry
**Purpose:** Track all trained models (TTS, ASR, LLM, NMT) with versioning and multi-language support

**Key Features:**
- Semantic versioning (v1.0.0, v1.1.0, v2.0.0)
- Multi-language associations (link by language_id)
- Performance metrics per language (WER, MOS, BLEU)
- Deployment status tracking
- Download with authentication
- Known issues tracking
- Docker image references

**Data Model:** `ml_models` collection
- See implementation plan for full schema
- Links to `languages` via `language_ids`
- Links to `ml_training_pipelines` via `pipeline_id`
- Links to `dataset_versions` via `training_datasets`

#### 1.2 Dataset Management
**Purpose:** Versioned dataset storage with integrity verification

**Key Features:**
- Semantic versioning with automatic incrementing
- Dataset splits (train/dev/test) tracking
- Quality reports per version
- Diff between versions (files added/removed/modified)
- Checksum verification (SHA256)
- Manifest-based file inventory
- Deprecation management

**Data Model:**
- `external_datasets` (enhanced with versioning)
- `dataset_versions` (version control)
- `storage_manifests` (file indexing)

#### 1.3 Training Pipeline Tracker
**Purpose:** MLflow-style pipeline tracking from data acquisition to deployment

**Key Features:**
- 5-stage pipeline: data_acquisition → preprocessing → training → evaluation → deployment
- Detailed metrics per stage
- Artifact management (datasets, models, reports)
- Checkpoint tracking
- Resource usage monitoring (GPU hours, cost)
- Team collaboration
- Reproducibility information (seed, framework versions)

**Data Model:** `ml_training_pipelines` collection
- Stage-by-stage progress tracking
- Preprocessing details (frequency, normalization, augmentations)
- Training config (epochs, batch size, optimizer)
- Evaluation plans
- Real-time status updates

#### 1.4 Community Contributions
**Purpose:** User uploads and external resource links

**Key Features:**
- File uploads (datasets, notebooks, resources)
- External link submissions (HuggingFace, GitHub, Kaggle, OpenSLR)
- Virus scanning and quarantine
- Processing status tracking
- Integration into main corpus
- License enforcement

**Data Models:**
- `file_uploads` - Track user uploads
- `resource_links` - External resource management
- Availability monitoring for links

### 2. Discovery & Search System

#### 2.1 Language Resource Hub
**Purpose:** One-stop shop for all resources related to a language

**Features:**
- All available datasets (audio, text, parallel)
- Pre-trained models (TTS, ASR, LLM)
- Training notebooks categorized by stage
- Active pipelines
- Resource gap indicators
- "Start Training" wizard

**API Endpoints:**
```
GET /api/v1/languages/{code}/resources      # All resources
GET /api/v1/languages/{code}/models         # Models
GET /api/v1/languages/{code}/datasets       # Datasets
GET /api/v1/languages/{code}/notebooks      # Notebooks
GET /api/v1/languages/{code}/pipelines      # Active pipelines
```

#### 2.2 Model Discovery
**Purpose:** Find models by language, type, performance

**Features:**
- Filter by model type (TTS, ASR, LLM, NMT)
- Filter by language family
- Filter by deployment status
- Sort by performance metrics
- Multi-language model highlighting

**API Endpoints:**
```
GET /api/v1/models                          # List all models
GET /api/v1/models/search                   # Advanced search
GET /api/v1/models/{uuid}                   # Model details
GET /api/v1/models/{uuid}/languages         # Supported languages
GET /api/v1/models/{uuid}/download          # Download model
```

#### 2.3 Universal Search
**Purpose:** Search across all entities (models, datasets, notebooks, links)

**Features:**
- Full-text search
- Faceted filtering
- Autocomplete suggestions
- Search by tags
- Result ranking by relevance

### 3. Version Control System

#### 3.1 Semantic Versioning
**Implementation:**
- Format: `MAJOR.MINOR.PATCH`
- MAJOR: Breaking changes (incompatible API changes)
- MINOR: New features (backward-compatible)
- PATCH: Bug fixes (backward-compatible)

**Utilities:**
```python
def compare_versions(v1, v2) -> int
def increment_version(version, bump_type) -> str
def is_compatible(v1, v2) -> bool
```

#### 3.2 Version Comparison
**Features:**
- Side-by-side diff view
- File-level changes (added/removed/modified)
- Performance metric comparison
- Changelog display
- Upgrade/downgrade recommendations

### 4. Access Control & Security

#### 4.1 Authentication Flow
- Supabase JWT tokens
- Role-based access control (contributor, validator, expert, admin)
- Token refresh mechanism
- Session management

#### 4.2 Download Authorization
- Pre-signed URLs with expiration
- Access logging
- Rate limiting (prevent abuse)
- License agreement enforcement

#### 4.3 Upload Security
- Virus scanning (ClamAV integration)
- File type validation
- Size limits enforcement
- Quarantine system
- Malware detection

### 5. Community Features (Existing)

#### 5.1 Gamification Engine
- Points for contributions and validations
- Achievement badges
- Leaderboards by language family
- Community levels (Newcomer → Contributor → Validator → Expert → Guardian)

#### 5.2 Real-time Collaboration
- WebSocket-powered live updates
- Language family chat rooms
- Validation notifications
- Activity feeds

#### 5.3 Quality Validation
- 3-tier system (Gold/Community/Submitted)
- Consensus-based promotion
- Expert validator assignment
- Quality scoring algorithms

---

## Database Schema

### NEW Collections (7)

1. **ml_models** - ML model registry
   - Unique index: `model_uuid`
   - Compound indexes: `(model_type, deployment_status)`, `(language_ids, model_type)`

2. **ml_training_pipelines** - Pipeline tracking
   - Unique index: `pipeline_uuid`
   - Compound indexes: `(is_active, current_stage)`, `(model_type, is_active)`

3. **dataset_versions** - Version control
   - Unique index: `(dataset_id, version)`
   - Indexes: `dataset_id`, `version`, `is_stable`, `is_deprecated`

4. **file_uploads** - User upload tracking
   - Unique index: `upload_uuid`
   - Compound indexes: `(uploaded_by, processing_status)`, `(upload_type, processing_status)`

5. **resource_links** - External resources
   - Unique index: `link_uuid`
   - Compound indexes: `(resource_type, verification_status)`, `(platform, resource_type)`

6. **model_language_associations** - Multi-language linking
   - Unique index: `(model_id, language_id)`
   - Indexes: `model_uuid`, `language_id`, `language_family_id`

7. **storage_manifests** - File system indexing
   - Unique index: `(entity_type, entity_id, version)`
   - Indexes: `entity_type`, `entity_id`, `storage_backend`

### ENHANCED Collections (3)

**external_datasets:**
- Added: `dataset_uuid`, `version`, `is_latest_version`, `version_history`
- Added: `storage_path`, `manifest_id`, `checksum`, `download_url`
- Added: `used_in_pipelines`, `used_in_models`, `training_ready`
- Added: `has_train_split`, `has_validation_split`, `has_test_split`
- Added: `download_count`, `view_count`, `citation_count`

**languages:**
- Added: `available_datasets`, `available_models`, `active_pipelines`
- Added: `total_audio_hours`, `total_text_samples`
- Added: `best_asr_wer`, `best_tts_mos`, `best_model_references`

**language_notebooks:**
- Added: `model_type`, `pipeline_stage`, `notebook_version`
- Added: `requirements` (dependencies, hardware, runtime)
- Added: `expected_outputs`, `produces_artifacts`
- Added: `execution_tested`, `last_successful_run`, `known_issues`
- Added: `storage_path`, `download_url`

---

## API Endpoints

### Models API (`/api/v1/models`)
```
POST   /api/v1/models                           # Register new model
GET    /api/v1/models                           # List models (filterable)
GET    /api/v1/models/{model_uuid}              # Get model details
PUT    /api/v1/models/{model_uuid}              # Update model
POST   /api/v1/models/{model_uuid}/versions     # Create new version
GET    /api/v1/models/{model_uuid}/download     # Download model (auth required)
POST   /api/v1/models/{model_uuid}/issues       # Report issue
GET    /api/v1/models/search                    # Advanced search
GET    /api/v1/models/{uuid}/languages          # Supported languages
```

### Pipelines API (`/api/v1/pipelines`)
```
POST   /api/v1/pipelines                        # Create pipeline
GET    /api/v1/pipelines                        # List pipelines
GET    /api/v1/pipelines/{id}                   # Get pipeline details
PUT    /api/v1/pipelines/{id}/stages/{stage}    # Update stage
POST   /api/v1/pipelines/{id}/artifacts         # Upload artifact
GET    /api/v1/pipelines/{id}/metrics           # Get metrics
POST   /api/v1/pipelines/{id}/complete          # Mark complete
```

### Dataset Versions API (`/api/v1/datasets`)
```
POST   /api/v1/datasets/{id}/versions           # Create new version
GET    /api/v1/datasets/{id}/versions           # List versions
GET    /api/v1/datasets/{id}/versions/{version} # Get specific version
GET    /api/v1/datasets/{id}/versions/{version}/download  # Download
GET    /api/v1/datasets/{id}/versions/{version}/diff      # Compare versions
```

### Resources API (`/api/v1/resources`)
```
POST   /api/v1/resources/links                  # Submit resource link
POST   /api/v1/resources/upload                 # Upload files
GET    /api/v1/resources/links                  # Browse links
POST   /api/v1/resources/links/{id}/verify      # Verify link
GET    /api/v1/resources/uploads/{id}           # Track upload status
```

### Discovery API (`/api/v1/languages`)
```
GET    /api/v1/languages/{code}/resources       # All resources for language
GET    /api/v1/languages/{code}/models          # Models for language
GET    /api/v1/languages/{code}/datasets        # Datasets for language
GET    /api/v1/languages/{code}/notebooks       # Notebooks for language
GET    /api/v1/languages/{code}/pipelines       # Active pipelines
GET    /api/v1/search                           # Universal search
```

### Existing APIs (Preserved)
```
# Language Management
GET    /api/v1/languages/families               # List language families
GET    /api/v1/languages/{code}                 # Get language details
GET    /api/v1/languages/search                 # Search languages

# Data Submission
POST   /api/v1/submit/audio                     # Submit audio data
POST   /api/v1/submit/text                      # Submit text content
POST   /api/v1/submit/link                      # Submit external links

# Validation
GET    /api/v1/validate/pending                 # Get pending validations
POST   /api/v1/validate/{id}                    # Submit validation review

# Community
GET    /api/v1/community/leaderboard            # Community leaderboard
WS     /api/v1/community/live/{family}          # Real-time collaboration
```

---

## Frontend Structure

### Existing Pages (Preserved)
1. **Index** (`/`) - Landing page with hero section
2. **Dashboard** (`/dashboard`) - User dashboard with statistics
3. **Languages** (`/languages`) - Browse languages and families
4. **LanguageDetail** (`/languages/:code`) - Language detail page
5. **LanguageFamilyDetail** (`/languages/families/:id`) - Family detail
6. **Submit** (`/submit`) - Submission forms (audio, text, link)
7. **Validate** (`/validate`) - Validation interface
8. **Community** (`/community`) - Leaderboards, chat, activity
9. **Moderation** (`/moderation`) - Content moderation tools
10. **Datasets** (`/datasets`) - **TO BE ENHANCED** with MLOps features
11. **Search** (`/search`) - Search interface
12. **Profile** (`/profile`) - User profile management
13. **NotFound** (`/404`) - 404 error page

### NEW Pages (To Be Added)
14. **Models** (`/models`) - Model browser and registry
15. **Pipelines** (`/pipelines`) - Pipeline tracker dashboard
16. **Notebooks** (`/notebooks`) - Notebook repository
17. **Resources** (`/resources`) - Resource links and contributions
18. **LanguageResources** (`/languages/:code/resources`) - Language resource hub

### Components to Enhance

#### Datasets Page Enhancement
**Current State:** Mock data, basic CRUD operations
**Enhancement Plan:**
- Replace mock data with real API calls
- Add version selector dropdown
- Display version comparison tool
- Show usage in models/pipelines
- Add authenticated download buttons
- Show dataset lineage graph

#### NEW Components to Create

1. **ModelBrowser** - Grid/list view of models
   - Filter by type, language, deployment status
   - Performance metrics cards
   - Download buttons with authentication
   - "Try in Playground" links

2. **PipelineTracker** - Visual pipeline progress
   - Stage progress indicators
   - Real-time metrics dashboard
   - Artifact browser
   - Resource usage charts
   - Team collaboration panel

3. **ResourceContribution** - Contribution forms
   - File upload (drag & drop)
   - External link submission
   - Notebook upload
   - License selector
   - Preview before submit

4. **LanguageResourceHub** - Comprehensive language page
   - Tabs: Datasets | Models | Notebooks | Pipelines
   - Resource gap indicators
   - "Start Training" wizard
   - Download statistics
   - Citation information

5. **VersionComparison** - Side-by-side version diff
   - File-level changes
   - Performance metric charts
   - Changelog display
   - Upgrade/downgrade recommendations

6. **PipelineStageDetails** - Stage detail modal
   - Configuration display
   - Metrics visualization
   - Artifact list
   - Logs viewer
   - Error reporting

---

## Implementation Priority

### Phase 1: Storage & Infrastructure (Weeks 1-2) ✅ COMPLETED
- [x] Hetzner Storage Box setup
- [x] Storage service layer (SFTP/WebDAV)
- [x] Manifest generation service
- [x] File integrity verification

### Phase 2: Database Migrations (Weeks 2-3) ✅ COMPLETED
- [x] Create 7 new collections with indexes
- [x] Enhance 3 existing collections
- [x] Create migration scripts
- [x] Create rollback scripts

### Phase 3: Pydantic Models (Week 3) ✅ COMPLETED
- [x] ml_models.py
- [x] training_pipeline_models.py
- [x] version_models.py
- [x] resource_models.py
- [x] Enhance dataset_models.py
- [x] Enhance language_models.py

### Phase 4: API Endpoints (Weeks 4-5) 🔄 NEXT
- [ ] Model management APIs
- [ ] Pipeline management APIs
- [ ] Dataset version APIs
- [ ] Resource & upload APIs
- [ ] Discovery APIs
- [ ] Update existing dataset APIs

### Phase 5: Frontend Integration (Weeks 6-7) ⏳ PENDING
- [ ] Update API client (`lib/api.ts`)
- [ ] Enhance Datasets page
- [ ] Create Models page
- [ ] Create Pipelines page
- [ ] Create Language Resource Hub
- [ ] Add version comparison UI
- [ ] Update navigation

### Phase 6: MLOps Integration (Week 8) ⏳ PENDING
- [ ] Experiment tracking
- [ ] Automated versioning
- [ ] Monitoring & alerts
- [ ] Performance dashboard

### Phase 7: Security & Testing (Week 9-10) ⏳ PENDING
- [ ] Authentication flow
- [ ] Download authorization
- [ ] Upload security (virus scan)
- [ ] Unit tests
- [ ] Integration tests
- [ ] Documentation

---

## Success Metrics

### User Engagement
- **Resource Discovery Time:** <30 seconds to find relevant resources
- **Contribution Rate:** 3x increase in user uploads
- **Download Volume:** Track authenticated downloads per resource
- **Community Activity:** Maintain real-time collaboration metrics

### Technical Performance
- **API Response Time:** <200ms for search queries
- **Pipeline Visibility:** 100% of active trainings tracked
- **Version Adoption:** 80% of datasets have 2+ versions
- **Storage Efficiency:** 30% reduction via deduplication

### Data Quality
- **Dataset Coverage:** At least 5 datasets per tier-1 language
- **Model Coverage:** At least 2 models per tier-1 language
- **Notebook Coverage:** At least 10 notebooks per tier-1 language
- **Validation Rate:** 90% of submissions validated within 48 hours

---

## Security & Compliance

### Data Protection
- **Encryption:** TLS 1.3 in-transit, AES-256 at-rest
- **Access Logging:** All downloads and uploads logged
- **Audit Trail:** Complete version history
- **Backup:** Daily Hetzner snapshots with 30-day retention

### Authentication & Authorization
- **JWT Tokens:** Supabase-issued tokens with refresh mechanism
- **Role-Based Access:** Contributor, Validator, Expert, Admin
- **Rate Limiting:** 100 requests/minute per user
- **License Enforcement:** Require agreement before download

### File Security
- **Virus Scanning:** ClamAV integration for all uploads
- **File Type Validation:** Whitelist of allowed MIME types
- **Size Limits:** 5GB per upload
- **Quarantine:** Automatic isolation of suspicious files

---

## Cost Estimate

### Monthly Operating Costs
- **Hetzner Storage Box (10TB):** €45/month
- **Bandwidth (2TB):** ~€20/month
- **MongoDB Atlas (Shared Cluster):** $0/month (free tier)
- **Supabase (Auth):** $0/month (free tier)
- **Redis (Upstash):** $0/month (free tier)
- **Total:** ~€65/month ($70/month)

### Scaling Projections
- **20TB Storage:** €90/month
- **5TB Bandwidth:** €50/month
- **MongoDB (M10):** $57/month
- **Total at scale:** ~$220/month

---

## Integration with Voice Lab

The platform directly feeds training data to voice-lab models:

**ASR Models:**
- Faster Whisper (akan-whisper)
- Wav2Vec2
- MMS

**TTS Models:**
- Kokoro
- F5-TTS
- OpenVoice
- ChatTTS
- StyleTTS2
- MeloTTS

**Audio-to-Audio:**
- Moshi (multi-African language system)

**Pipeline Integration:**
1. Community collects data → Platform validates & versions
2. Data scientist discovers datasets → Downloads via authenticated API
3. Training pipeline tracked → Metrics logged to platform
4. Model registered → Performance benchmarks stored
5. Model deployed → Integration with voice-lab endpoints

---

## Migration Strategy

### Data Migration
1. **Create v1.0.0 for all existing datasets**
2. **Generate storage manifests for current files**
3. **Move files to new Hetzner structure** (preserve old paths for 30 days)
4. **Update language references with resource lists**
5. **Create initial model records for voice-lab models**
6. **Link languages to models via model_language_associations**

### Rollback Plan
- Keep old collections for 30 days
- Dual-write during transition period
- Gradual frontend migration with feature flags
- Ability to revert to old API endpoints

### Testing Strategy
- Run migration on staging database first
- Verify all relationships preserved
- Test download flows end-to-end
- Validate file integrity with checksums

---

## Non-Functional Requirements

### Performance
- API response time: <200ms (p95), <500ms (p99)
- File upload: Support up to 5GB files
- Concurrent users: Support 1000+ simultaneous users
- Database queries: All indexed queries <50ms

### Scalability
- Horizontal scaling via load balancer
- MongoDB sharding for large collections
- CDN for static assets
- Hetzner Storage Box can scale to 100TB

### Reliability
- 99.9% uptime SLA
- Automated health checks
- Graceful degradation
- Circuit breakers for external services

### Maintainability
- Comprehensive API documentation (OpenAPI/Swagger)
- Type safety (Pydantic, TypeScript)
- Automated testing (>80% coverage)
- Code review process
- Migration versioning

---

## Future Enhancements (Post-MVP)

### Phase 2 Features
- **Automated Quality Checks:** AI-powered audio quality assessment
- **Collaborative Annotation:** Multi-user annotation tools
- **Data Augmentation Pipeline:** Built-in augmentation tools
- **Model Serving:** Direct model inference API
- **Experiment Tracking:** MLflow integration
- **CI/CD for Models:** Automated training pipelines
- **Data Lineage Visualization:** Interactive dependency graphs
- **Performance Benchmarking:** Automated model comparison

### Long-term Vision
- **Mobile App:** Native iOS/Android apps for field data collection
- **Discord Bot:** Quick submit via Discord
- **Browser Extension:** Capture language content while browsing
- **API Marketplace:** Allow third-party integrations
- **Distributed Training:** Multi-node training coordination
- **Federated Learning:** Privacy-preserving training

---

## Appendix

### Glossary
- **MLOps:** Machine Learning Operations - practices for deploying and maintaining ML systems
- **Semantic Versioning:** Version numbering scheme (MAJOR.MINOR.PATCH)
- **Manifest:** File inventory with checksums and metadata
- **Pipeline Stage:** Step in ML workflow (data acquisition, preprocessing, training, evaluation, deployment)
- **Tier System:** Quality classification (Gold/Community/Submitted)
- **Language Family:** Linguistic grouping (Niger-Congo, Afroasiatic, etc.)

### References
- [Original Implementation Plan](#) - See TASK.md
- [Database Schema](#) - See migration scripts
- [API Documentation](#) - Available at `/docs` endpoint
- [Frontend Components](#) - See src/components/
- [Pydantic Models](#) - See backend/models/

---

**Document Owner:** Development Team
**Stakeholders:** Community Contributors, ML Researchers, Voice Lab Team
**Review Cycle:** Monthly or on major feature releases

---

*This PRD serves as the north star for the African Language Community Platform development, ensuring all team members are aligned on vision, architecture, and implementation priorities.*
