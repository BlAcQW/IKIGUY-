# InkWave Time Tracking - Test Instructions

**Date:** December 2, 2025
**Feature:** Accurate listening time tracking for analytics

---

## ✅ **Implementation Summary**

The time tracking system has been successfully implemented with the following changes:

### **Frontend Changes:**

1. **`useChunkPlayer` Hook** (`src/hooks/useChunkPlayer.ts`)
   - ✅ Added `totalListeningMinutes` state
   - ✅ Added time tracking effect that runs every second during playback
   - ✅ Accumulates seconds and converts to minutes every 60 seconds
   - ✅ Updated `onProgressUpdate` callback to include `totalTimeMinutes` parameter
   - ✅ Progress updates sent every 10 seconds during playback
   - ✅ Progress saved immediately on pause

2. **API Client** (`src/lib/api.ts`)
   - ✅ Updated `api.reading.updateProgress()` to accept optional `totalTimeMinutes` parameter
   - ✅ Only sends `total_time_spent_minutes` if value is defined

3. **PlayerPageRedesign** (`src/pages/PlayerPageRedesign.tsx`)
   - ✅ Updated to pass `totalTimeMinutes` to the API

### **Backend Status:**
- ✅ Already supports `total_time_spent_minutes` in reading sessions
- ✅ Analytics endpoints correctly aggregate time data
- ✅ Database schema ready (field exists in `reading_sessions` collection)

---

## 🧪 **Testing Instructions**

### **Test 1: Manual Playback Test (5 minutes)**

1. **Access InkWave:**
   ```
   https://inkwave.ailabsafrica.com
   ```

2. **Login:**
   - Email: `admin@ailabsafrica.com`
   - Password: Use your admin password

3. **Start Playing a Book:**
   - Navigate to any book
   - Click "Start Listening" or "Play"
   - Let the audio play for **at least 2 minutes**

4. **Verify Database Updates:**
   ```bash
   mongosh "mongodb://admin:aawwER4444%@127.0.0.1:27017/inkwave?authSource=admin" \
     --eval "db.reading_sessions.find({total_time_spent_minutes: {\$gt: 0}}).pretty()"
   ```

   **Expected Result:**
   ```javascript
   {
     session_id: '...',
     user_id: '4a6252e7-3dc7-483a-92c3-59a0a814a169',
     book_id: 'book_...',
     total_time_spent_minutes: 2,  // ✅ Should be > 0!
     last_accessed: ISODate('2025-12-02T...')
   }
   ```

5. **Check Analytics Dashboard:**
   - Navigate to Admin Analytics
   - Verify "Narration Minutes" shows > 0
   - Check user analytics table for listening time

---

### **Test 2: Time Accumulation Test (10 minutes)**

1. **Play a book for 1 minute** → Pause
2. **Check database** - should show `~1 minute`
3. **Resume playback for another 2 minutes** → Pause
4. **Check database again** - should show `~3 minutes` (accumulated)

**Verification:**
```bash
# Get specific session
mongosh "mongodb://admin:aawwER4444%@127.0.0.1:27017/inkwave?authSource=admin" \
  --eval "db.reading_sessions.findOne({user_id: '4a6252e7-3dc7-483a-92c3-59a0a814a169'})"
```

---

### **Test 3: Analytics Endpoint Test**

**Test Admin Analytics:**
```bash
TOKEN="<your_admin_token>"

curl -H "Authorization: Bearer $TOKEN" \
  "https://inkwave-api.ailabsafrica.com/api/v1/admin/analytics?period=day"
```

**Expected Response:**
```json
{
  "narration_minutes": 15,  // ✅ Should be > 0
  "total_events": 5,
  "active_users": 2,
  ...
}
```

**Test User Analytics:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "https://inkwave-api.ailabsafrica.com/api/v1/admin/analytics/users?limit=10&sort_by=usage"
```

**Expected Response:**
```json
{
  "users": [
    {
      "user_id": "4a6252e7-3dc7-483a-92c3-59a0a814a169",
      "email": "admin@ailabsafrica.com",
      "total_listening_minutes": 15,  // ✅ Should be > 0
      "unique_books_count": 3,
      "sessions_count": 5
    }
  ]
}
```

---

## 🔍 **Debugging Steps**

### **If Time is Still 0:**

1. **Check Browser Console:**
   - Open DevTools → Console
   - Look for progress update calls:
   ```javascript
   // Should see logs like:
   PUT /reading/sessions/{id}
   {
     current_chunk_index: 0,
     current_position_seconds: 5.2,
     total_time_spent_minutes: 2  // ✅ This should be present!
   }
   ```

2. **Check Network Tab:**
   - Filter for `reading/sessions`
   - Inspect request payload
   - Verify `total_time_spent_minutes` is being sent

3. **Check Backend Logs:**
   ```bash
   sudo journalctl -u kasaai-inkwave-backend -f
   ```
   - Look for session update logs
   - Verify no errors during update

4. **Verify Player is Active:**
   - Make sure you're using PlayerPageRedesign (not LibbyPlayer)
   - Check that audio is actually playing (not paused)
   - Verify `useChunkMode` is `true`

---

## 📊 **Expected Analytics After Fix**

Once users have been listening for a while, analytics should show:

### **Admin Dashboard:**
- ✅ **Narration Minutes:** Sum of all listening time across users
- ✅ **Total Reading Time:** Same as narration minutes
- ✅ **Average Session Duration:** Total time / number of sessions

### **User Analytics:**
- ✅ **Total Listening Minutes:** Per user (sorted by usage)
- ✅ **Most Active Users:** Based on listening time
- ✅ **Listening Trends:** Time series data

### **Book Analytics:**
- ✅ **Most Listened Books:** By total minutes (not just play count)
- ✅ **Average Completion Rate:** Based on time vs. book duration

---

## 🎯 **Success Criteria**

The implementation is successful if:

1. ✅ Time tracking updates every second during playback
2. ✅ Progress saved to database every 10 seconds (or on pause)
3. ✅ `total_time_spent_minutes` field in database shows non-zero values
4. ✅ Analytics dashboard displays accurate listening time
5. ✅ Time accumulates across multiple sessions
6. ✅ No errors in console or backend logs

---

## 🐛 **Known Limitations**

1. **Time Precision:** Time is tracked in minutes (not seconds) for database storage
2. **Rounding:** Partial minutes are accumulated but only full minutes are saved
3. **Session-Based:** Time is per session, not global (by design)

---

## 🔧 **Manual Database Fix (If Needed)**

If you need to manually set time for testing:

```javascript
// Connect to MongoDB
mongosh "mongodb://admin:aawwER4444%@127.0.0.1:27017/inkwave?authSource=admin"

// Update a session with test time
db.reading_sessions.updateOne(
  { user_id: '4a6252e7-3dc7-483a-92c3-59a0a814a169' },
  { $set: { total_time_spent_minutes: 25 } }
)

// Verify update
db.reading_sessions.findOne({ user_id: '4a6252e7-3dc7-483a-92c3-59a0a814a169' })
```

---

## 📝 **Next Steps**

1. **Test the implementation** following the instructions above
2. **Monitor analytics** over the next few days
3. **Verify accuracy** by comparing tracked time with actual listening
4. **Report any issues** if time tracking doesn't work as expected

---

## 🚀 **Deployment Status**

- ✅ Frontend built and deployed (December 2, 2025)
- ✅ Backend ready (no changes needed)
- ✅ Database schema ready
- ✅ All code changes committed

**Ready for production testing!**
