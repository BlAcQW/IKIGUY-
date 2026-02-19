# Creating Announcements

This document describes how to create announcements that will appear on the landing page.

## Method 1: Using the Admin Interface (Recommended)

1. Navigate to `/admin/announcements`
2. Click "Create Announcement"
3. Fill in the form:
   - **Title**: Announcement title (required)
   - **Description**: Detailed description (optional)
   - **Image**: Upload an image (optional, recommended)
   - **CTA Button Text**: Text for the call-to-action button (e.g., "Register Now")
   - **CTA Button Link**: Where the button should link to (e.g., "/events", "/portal")
   - **Event ID**: Optional link to specific event/conference
   - **Start Date**: When to start showing the announcement (optional)
   - **End Date**: When to stop showing the announcement (optional)
   - **Display Order**: Lower numbers appear first (0 = highest priority)
   - **Active**: Toggle visibility
4. Click "Create Announcement"

## Method 2: Using the API

You can create announcements programmatically via the API:

### Endpoint
```
POST /api/v1/announcements
```

### Headers
```
Authorization: Bearer <admin_token>
Content-Type: application/json
```

### Request Body
```json
{
  "title": "31st December Crossover Service",
  "description": "Join us for a powerful night of worship, prayer, and prophecy...",
  "image_url": "https://example.com/image.jpg",
  "cta_text": "Register Now",
  "cta_link": "/events",
  "event_id": "optional_event_id",
  "is_active": true,
  "display_order": 1,
  "start_date": "2024-12-01T00:00:00Z",
  "end_date": "2024-12-31T23:59:59Z"
}
```

### Example: 31st December Crossover Service

```bash
curl -X POST "https://churchflow.ailabsafrica.com/api/v1/announcements" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "31st December Crossover Service",
    "description": "Join us for a powerful night of worship, prayer, and prophecy as we cross over into the new year. This is a special service to give thanks for the past year and receive direction for the year ahead.",
    "cta_text": "Register Now",
    "cta_link": "/events",
    "is_active": true,
    "display_order": 1,
    "start_date": "2024-12-01T00:00:00Z",
    "end_date": "2024-12-31T23:59:59Z"
  }'
```

## Image Upload

To upload an image for an announcement:

1. Use the admin interface and click "Click to upload image" in the form
2. Or use the image upload endpoint:

```
POST /api/v1/announcements/upload-image
```

**Form Data:**
- `file`: Image file (JPEG, PNG, GIF, WebP, max 10MB)

**Response:**
```json
{
  "image_url": "/storage/announcements/filename.jpg"
}
```

Then use this `image_url` when creating/updating the announcement.

## Best Practices

1. **Use compelling images** - Images make announcements more engaging
2. **Set date ranges** - Use start_date and end_date to automatically show/hide announcements
3. **Order by priority** - Use display_order to control which announcements appear first
4. **Clear CTAs** - Make call-to-action buttons clear and actionable
5. **Link to relevant pages** - Use cta_link to guide users to the right place (events, portal, giving, etc.)

## Display on Landing Page

Announcements are automatically displayed on the landing page (`/`) in the "Announcements" section, which appears before the "Upcoming Events" section.

Only active announcements within their date ranges are shown to the public via the `/api/v1/announcements/public` endpoint.

