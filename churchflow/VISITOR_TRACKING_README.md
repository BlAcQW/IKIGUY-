# ChurchFlow Visitor Tracking & Discipleship System

Complete system for capturing first-timers, tracking discipleship journeys, and enabling data enrichment by church leaders with automated multi-channel communications.

## Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [User Roles & Permissions](#user-roles--permissions)
- [Journey Types](#journey-types)
- [API Endpoints](#api-endpoints)
- [Usage Guide](#usage-guide)
- [Communication Automation](#communication-automation)
- [Data Enrichment & Audit Trail](#data-enrichment--audit-trail)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

---

## Overview

The Visitor Tracking & Discipleship System enables churches to:

✅ **Capture first-timers and new converts every Sunday**
✅ **Assign visitors to cell leaders with hierarchical oversight**
✅ **Send automated communications (SMS, WhatsApp, Voice)**
✅ **Track members through discipleship stages**
✅ **Enable data enrichment by assigned leaders**
✅ **Monitor journey analytics and conversion funnels**

### Key Features

- **Hierarchical Permissions**: Admin → Zone Leader → Cell Leader → Department Head
- **Multi-Channel Communications**: SMS, WhatsApp, Voice (VAPI integration)
- **Three Journey Types**: Spiritual, Cell Group, Ministry/Department
- **Full Audit Trail**: Track who enriched what data and when
- **Life Event Tracking**: Record births, deaths, marriages, illness, celebrations
- **Automated Follow-ups**: Schedule communications based on journey stage
- **Analytics Dashboard**: Stage funnels, conversion rates, retention metrics

---

## System Architecture

### Data Models

**Enhanced User Model** - Extends existing user with:
- `member_status`: visitor | active_member | inactive_member | alumni
- `current_spiritual_stage`, `current_cell_stage`, `current_ministry_stage`
- `cell_group_id`, `assigned_cell_leader_id`, `zone_id`
- `stage_history[]`: Complete audit trail of journey progression
- `enrichment_history[]`: Who updated what data and when
- `life_events[]`: Significant events requiring pastoral care

**Organizational Structure**:
- `CellGroup`: Small groups with cell leaders
- `Zone`: Collection of cell groups with zone leaders
- `Department`: Ministry teams with department heads

**Journey Configuration**:
- `JourneyStage`: Configurable stages with automation triggers
- `ScheduledCommunication`: Queued messages with retry logic

### Core Services

1. **VisitorService** - Capture, assign, welcome communications
2. **DiscipleshipService** - Stage progression, analytics, follow-ups
3. **LeadershipService** - Cell groups, zones, permissions
4. **EnrichmentService** - Data updates, life events, audit trail
5. **CommunicationOrchestrationService** - Multi-channel messaging
6. **SchedulerService** - Background job processing (APScheduler)

---

## User Roles & Permissions

### Role Hierarchy

```
Universal Admin
    ↓
Admin (per organization)
    ↓
Zone Leader (oversees zones)
    ↓
Cell Leader (oversees cell groups)
    ↓
Department Head (oversees departments)
    ↓
Member
```

### Permission Matrix

| Action | Cell Leader | Zone Leader | Department Head | Admin |
|--------|-------------|-------------|-----------------|-------|
| View assigned members | ✅ | ✅ | ✅ | ✅ |
| View zone members | ❌ | ✅ | ❌ | ✅ |
| View all members | ❌ | ❌ | ❌ | ✅ |
| Enrich member data | ✅ | ✅ | ✅ | ✅ |
| Advance journey stage | ✅ | ✅ | ❌ | ✅ |
| Assign to cell group | ❌ | ✅ | ❌ | ✅ |
| Create cell group | ❌ | ✅ | ❌ | ✅ |
| Send bulk communications | ✅ | ✅ | ✅ | ✅ |

---

## Journey Types

### 1. Spiritual Journey

Tracks conversion and baptism pathway:

```
First Timer (order: 1)
    ↓
Second Timer (order: 2)
    ↓
Regular Attendee (order: 3)
    ↓
New Convert (order: 4)
    ↓
Baptism Class (order: 5)
    ↓
Baptized (order: 6)
```

**Automated Communications**:
- First Timer: Welcome SMS + WhatsApp (5min delay), Day 1 SMS, Day 3 Voice call, Day 7 WhatsApp
- New Convert: Baptism class invitation (Day 1), Check-in call (Day 7)
- Baptism Class: Class reminders, Baptism date notification

### 2. Cell Journey

Tracks cell group integration:

```
Cell Visitor (order: 1)
    ↓
Cell Member (order: 2)
    ↓
Cell Leader-in-Training (order: 3)
    ↓
Cell Leader (order: 4)
```

### 3. Ministry Journey

Tracks ministry/department involvement:

```
Department Volunteer (order: 1)
    ↓
Department Leader (order: 2)
    ↓
Ministry Leader (order: 3)
```

---

## API Endpoints

### Visitor Capture

```http
POST /api/churchflow/visitors
Authorization: Bearer {token}
Content-Type: application/json

{
  "phone": "+233244123456",
  "name": "John Mensah",
  "email": "john@example.com",
  "first_visit_source": "friend_referral",
  "send_immediate_welcome": true
}
```

**Response**:
```json
{
  "id": "507f1f77bcf86cd799439011",
  "phone": "+233244123456",
  "name": "John Mensah",
  "member_status": "visitor",
  "current_spiritual_stage": "first_timer",
  "visit_count": 1,
  "first_visit_date": "2025-12-03T10:00:00",
  "scheduled_communications": [
    {
      "delay_days": 1,
      "channels": ["sms"]
    }
  ]
}
```

### Assign to Cell Group

```http
POST /api/churchflow/cell-groups/{cell_id}/assign-member
Authorization: Bearer {token}

{
  "user_id": "507f1f77bcf86cd799439011"
}
```

### Advance Journey Stage

```http
POST /api/churchflow/journey/advance
Authorization: Bearer {token}

{
  "user_id": "507f1f77bcf86cd799439011",
  "journey_type": "spiritual",
  "new_stage": "new_convert",
  "notes": "Gave life to Christ during altar call"
}
```

### Enrich Member Data

```http
PUT /api/churchflow/members/{user_id}/enrich
Authorization: Bearer {token}

{
  "field_updates": {
    "occupation": "Teacher",
    "marital_status": "married",
    "address": "123 Main Street, Accra"
  },
  "notes": "Updated during home visit"
}
```

### Record Life Event

```http
POST /api/churchflow/members/{user_id}/life-events
Authorization: Bearer {token}

{
  "event_type": "birth",
  "event_date": "2025-11-15T00:00:00",
  "description": "Welcomed baby girl - Sarah",
  "requires_followup": true
}
```

### Get Journey Analytics

```http
GET /api/churchflow/journey/analytics/funnel?journey_type=spiritual
Authorization: Bearer {token}
```

**Response**:
```json
{
  "journey_type": "spiritual",
  "total_members": 150,
  "funnel": [
    {"stage_name": "first_timer", "count": 50, "percentage": 33},
    {"stage_name": "second_timer", "count": 30, "percentage": 20},
    {"stage_name": "new_convert", "count": 25, "percentage": 17},
    {"stage_name": "baptism_class", "count": 20, "percentage": 13},
    {"stage_name": "baptized", "count": 25, "percentage": 17}
  ],
  "conversion_rates": {
    "first_timer_to_second_timer": 60,
    "new_convert_to_baptized": 100
  }
}
```

For complete API documentation, see [API Endpoints Reference](../backend/app/api/routes/README.md).

---

## Usage Guide

### Capturing Visitors (Sunday Service)

1. **Coordinator/Cell Leader** captures visitor via mobile app or portal
2. Visitor receives **automatic welcome message** (SMS + WhatsApp)
3. System schedules **follow-up communications** (Day 1, 3, 7)
4. Coordinator assigns visitor to **available cell group**
5. **Cell leader** receives notification of new assignment

### Cell Leader Follow-up Workflow

1. View **assigned members** dashboard
2. See **pending follow-ups** (life events, birthdays, absences)
3. **Enrich member data** after home visits
4. **Record life events** (births, marriages, illness)
5. **Advance members** through journey stages
6. Send **manual communications** for special occasions

### Zone Leader Oversight

1. View **all cell groups in zone**
2. Monitor **stage progression metrics**
3. Identify **stagnant members** (no progression in 30+ days)
4. Create **zone-wide campaigns** for specific stages
5. **Assign new cell leaders** as groups grow

### Admin Analytics

1. View **journey funnels** across all three journeys
2. Monitor **conversion rates** between stages
3. Identify **drop-off points** in discipleship pathway
4. Track **communication effectiveness** (SMS vs WhatsApp vs Voice)
5. Generate **monthly reports** for church leadership

---

## Communication Automation

### Trigger Types

1. **Immediate Welcome** - Sent 5-15 minutes after visitor capture
2. **Scheduled Follow-ups** - Based on delay_days in journey stage config
3. **Stage Transition** - Triggered when advancing to new stage
4. **Manual Send** - Cell leaders sending targeted messages
5. **Bulk Campaigns** - Communications to all members at specific stage

### Message Template Variables

Available variables for dynamic personalization:

- `{{name}}` - Member's name
- `{{church_name}}` - Church/organization name
- `{{cell_leader}}` - Cell leader's name
- `{{meeting_day}}` - Cell meeting day
- `{{meeting_time}}` - Cell meeting time
- `{{baptism_date}}` - Upcoming baptism date
- `{{class_day}}` - Baptism class day

**Example**:
```
Hi {{name}}! Welcome to {{church_name}}!
Your cell leader {{cell_leader}} will reach out soon.
Cell meetings are every {{meeting_day}} at {{meeting_time}}.
```

### Communication Channels

| Channel | Use Case | Cost | Delivery Rate |
|---------|----------|------|---------------|
| **SMS** | Quick notifications, reminders | Low | 95%+ |
| **WhatsApp** | Rich content, images, links | Low | 90%+ |
| **Voice** | Personal touch, urgent follow-up | Medium | 60-70% |

### Deduplication Logic

Prevents message spam:
- No duplicate messages within **24 hours** of same type
- Cell leader manual sends **bypass deduplication**
- Bulk campaigns check for **recent communications**

---

## Data Enrichment & Audit Trail

### Enrichable Fields

**Extended Profile**:
- `date_of_birth`, `gender`, `occupation`
- `marital_status`, `address`
- `emergency_contact_name`, `emergency_contact_phone`

**Basic Info**:
- `email`, `full_name`

**Preferences**:
- `preferred_communication_channel` (sms | whatsapp | voice | email)

**Location**:
- `branch_id`

### Audit Trail Example

```json
{
  "enrichment_history": [
    {
      "field_name": "occupation",
      "previous_value": null,
      "new_value": "Teacher",
      "enriched_by_user_id": "507f1f77bcf86cd799439012",
      "enriched_by_role": "cell_leader",
      "enriched_at": "2025-12-03T14:30:00",
      "notes": "Home visit - verified employment"
    }
  ]
}
```

### Life Event Types

- **birth** - Birth of child
- **death** - Death of family member
- **marriage** - Wedding ceremony
- **job_change** - New job or job loss
- **relocation** - Moving to new location
- **illness** - Serious illness requiring prayer/support
- **celebration** - Achievement, graduation, promotion
- **other** - Other significant events

### Follow-up Tracking

```json
{
  "life_events": [
    {
      "event_type": "illness",
      "event_date": "2025-11-20",
      "description": "Mother hospitalized - needs prayer",
      "requires_followup": true,
      "followup_completed": false,
      "recorded_by_user_id": "507f1f77bcf86cd799439012",
      "recorded_at": "2025-11-20T09:00:00"
    }
  ]
}
```

---

## Testing

### Running Tests

```bash
# All tests
pytest tests/

# Unit tests only
pytest tests/test_visitor_service.py
pytest tests/test_discipleship_service.py
pytest tests/test_leadership_service.py
pytest tests/test_enrichment_service.py

# Integration tests
pytest tests/test_visitor_journey_integration.py

# Specific test
pytest tests/test_visitor_service.py::test_capture_new_visitor -v
```

### Test Coverage

**Unit Tests** (59 tests):
- VisitorService: 14 tests
- DiscipleshipService: 14 tests
- LeadershipService: 15 tests
- EnrichmentService: 16 tests

**Integration Tests** (4 workflows):
- Complete visitor to baptized journey
- Cell leader permissions
- Life events and follow-ups
- Multi-journey progression

### Sample Test Data

```bash
# Seed default journey stages
python scripts/seed_default_journey_stages.py

# Seed with specific organization
python scripts/seed_default_journey_stages.py --organization-id 507f1f77bcf86cd799439011
```

---

## Troubleshooting

### Common Issues

#### 1. Welcome Message Not Sent

**Symptoms**: Visitor captured but no welcome communication received

**Causes**:
- `send_immediate_welcome` set to `false` in request
- `allow_automated_communications` set to `false` in user profile
- Communication service not initialized

**Solution**:
```python
# Check user preferences
user = await user_service.get_user_by_id(user_id)
print(user.allow_automated_communications)

# Manually trigger welcome
await visitor_service.send_welcome_communication(user, stage, org_id)
```

#### 2. Permission Denied Errors

**Symptoms**: `403 Access denied: Cell Leader or above required`

**Causes**:
- User missing required role in `roles` array
- User not assigned as cell leader to target member
- Hierarchical relationship not established

**Solution**:
```python
# Verify user roles
user = await user_service.get_user_by_id(cell_leader_id)
print(user.roles)  # Should include "cell_leader"

# Verify assignment
member = await user_service.get_user_by_id(member_id)
print(member.assigned_cell_leader_id == cell_leader_id)
```

#### 3. Scheduled Communications Not Processing

**Symptoms**: Messages stuck in "pending" status past scheduled time

**Causes**:
- SchedulerService not running
- Background job processor paused
- Database connection issues

**Solution**:
```bash
# Check scheduler status
sudo systemctl status kasaai-churchflow-backend

# View recent logs
sudo journalctl -u kasaai-churchflow-backend -f

# Restart service
sudo systemctl restart kasaai-churchflow-backend
```

#### 4. Stage Advancement Fails

**Symptoms**: `ValueError: Stage new_convert not found`

**Causes**:
- Journey stage not seeded in database
- Wrong organization_id
- Stage inactive or deleted

**Solution**:
```bash
# Re-seed journey stages
python scripts/seed_default_journey_stages.py

# Verify stages in database
mongosh churchflow
db.journey_stages.find({journey_type: "spiritual"}).pretty()
```

### Debugging Tips

**Enable Debug Logging**:
```python
# In app/core/config.py
debug = True  # Set to True for verbose logging
```

**Check Database Indexes**:
```javascript
// MongoDB shell
db.users.getIndexes()
db.cell_groups.getIndexes()
db.journey_stages.getIndexes()
```

**Monitor Scheduled Jobs**:
```javascript
// MongoDB shell - check APScheduler jobs
db.apscheduler_jobs.find().pretty()
```

**View Communication Queue**:
```javascript
// MongoDB shell - check pending communications
db.scheduled_communications.find({status: "pending"}).count()
db.scheduled_communications.find({status: "failed"}).pretty()
```

---

## Performance Optimization

### Recommended Indexes

Already created by `init_indexes()`:

```javascript
// Users collection
db.users.createIndex({"organization_id": 1, "member_status": 1})
db.users.createIndex({"organization_id": 1, "current_spiritual_stage": 1})
db.users.createIndex({"cell_group_id": 1})
db.users.createIndex({"assigned_cell_leader_id": 1})

// Scheduled communications
db.scheduled_communications.createIndex({"scheduled_for": 1, "status": 1})
db.scheduled_communications.createIndex({"organization_id": 1, "user_id": 1})
```

### Scaling Considerations

**For 1,000+ visitors/month**:
- Consider Redis caching for frequent queries
- Batch process scheduled communications
- Archive completed communications monthly

**For 10,000+ members**:
- Implement read replicas for analytics queries
- Use aggregation pipelines instead of application-level filtering
- Consider time-series collections for engagement metrics

---

## Future Enhancements

### Planned Features

- [ ] WhatsApp Business API integration (template messages)
- [ ] Advanced analytics dashboard (Power BI integration)
- [ ] Mobile app for cell leaders (React Native)
- [ ] Automated absence detection and re-engagement campaigns
- [ ] Integration with church calendar for event-based communications
- [ ] Member self-service portal for profile updates
- [ ] Multi-language support for communications
- [ ] AI-powered communication timing optimization

---

## Support & Contributing

### Getting Help

- **Documentation**: `/opt/kasaai/apps/churchflow/README.md`
- **API Docs**: `https://churchflow-api.ailabsafrica.com/api/churchflow/docs`
- **Issues**: GitHub Issues or internal support channel

### Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for:
- Code style guidelines
- Pull request process
- Testing requirements
- Commit message conventions

---

## License

Copyright © 2025 AI Labs Africa. All rights reserved.

For commercial licensing inquiries, contact: licensing@ailabsafrica.com

---

**Last Updated**: December 3, 2025
**Version**: 1.0.0
**Status**: Production Ready ✅
