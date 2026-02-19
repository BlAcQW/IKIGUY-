# TimePicker User Guide

## Quick Start

The enhanced TimePicker makes selecting session times faster and easier with quick presets and smart validation.

## How to Use

### Creating a New Session

1. **Navigate to Conference Sessions**
   - Open a conference
   - Click "Manage Sessions"
   - Click "+ Add Session"

2. **Select Start Time**
   - Click on the "Start Time" field
   - Dropdown opens with preset times
   - Click a preset (e.g., "9:00 AM") or enter custom time
   - Times after the End Time are disabled

3. **Select End Time**
   - Click on the "End Time" field
   - Dropdown shows only times after Start Time
   - Click a preset or enter custom time

4. **Save**
   - Click "Create Session"
   - Times are validated and saved

### Editing an Existing Session

1. **Open Session Details**
   - Click on any session card
   - Or navigate to session detail page

2. **Click Edit Button**
   - Modal opens with current values

3. **Change Times**
   - Click on time fields to open picker
   - Select new times from presets
   - Validation ensures end > start

4. **Save Changes**
   - Click "Save"
   - Updated times are applied

## Features Explained

### Quick Presets

**Available Times:**
```
Morning:    6:00 AM - 11:00 AM (hourly)
Noon:       12:00 PM
Afternoon:  1:00 PM - 5:00 PM (hourly)
Evening:    6:00 PM - 10:00 PM (hourly)
```

**Usage:**
- Click any preset for instant selection
- No typing required for common times
- Filtered based on min/max constraints

### Format Toggle

**12-Hour Format (Default):**
```
9:00 AM
2:00 PM
```

**24-Hour Format:**
```
09:00
14:00
```

**How to Toggle:**
1. Open dropdown
2. Click "12h" or "24h" button at top
3. Display updates immediately

### Custom Time Input

**For Precise Times:**
1. Open dropdown
2. Use "Custom Time" input field
3. Type exact time (e.g., 9:15 AM)
4. Click outside or press Enter

**Supported Formats:**
- HH:MM (24-hour)
- Browser native time picker

### Smart Validation

**Automatic Constraints:**

**Start Time Field:**
- Can't select times after End Time
- Presets after End Time are hidden
- Validation message shows if violated

**End Time Field:**
- Can't select times before Start Time
- Presets before Start Time are hidden
- Validation message shows if violated

**Example:**
```
Start Time: 9:00 AM
End Time:   Must be 10:00 AM or later

Start Time: Must be 1:00 PM or earlier
End Time:   2:00 PM
```

## Common Scenarios

### Morning Service

**Times:** 9:00 AM - 11:00 AM

**Steps:**
1. Start Time → Click "9:00 AM" preset
2. End Time → Click "11:00 AM" preset
3. Done in 2 clicks!

### All-Day Conference Session

**Times:** 8:00 AM - 5:00 PM

**Steps:**
1. Start Time → Use custom input: "08:00"
2. End Time → Click "5:00 PM" preset

### Evening Prayer Meeting

**Times:** 7:00 PM - 9:00 PM

**Steps:**
1. Start Time → Click "7:00 PM" preset
2. End Time → Click "9:00 PM" preset

### Workshop with Break

**Session 1:** 2:00 PM - 3:30 PM
**Break:** 3:30 PM - 4:00 PM
**Session 2:** 4:00 PM - 6:00 PM

**Steps:**
1. Create Session 1:
   - Start: "2:00 PM" preset
   - End: Custom "3:30 PM"

2. Create Session 2:
   - Start: "4:00 PM" preset
   - End: "6:00 PM" preset

## Keyboard Shortcuts

### Navigation
- **Tab**: Move to next field
- **Shift + Tab**: Move to previous field
- **Escape**: Close dropdown
- **Enter**: Confirm selection

### Dropdown
- **Arrow Up/Down**: Navigate presets
- **Enter**: Select highlighted preset
- **Space**: Select highlighted preset

## Mobile Usage

### Touch Targets
- All buttons are minimum 44px for easy tapping
- Large preset buttons for finger-friendly selection
- Swipe to scroll through presets

### Tips
- Use presets instead of typing on mobile
- Dropdown is optimized for small screens
- Native time picker available in custom input

## Accessibility

### Screen Readers
- ARIA labels on all interactive elements
- Validation messages announced
- Current selection announced
- Dropdown state changes announced

### Keyboard Only
- Full keyboard navigation support
- Tab order is logical
- Focus indicators visible
- No mouse required

### Visual
- High contrast labels
- Clear validation messages
- Icon indicators (clock)
- Disabled state is visually distinct

## Tips & Tricks

### Fastest Input Method
1. **Use presets** for hourly times (9:00, 10:00, etc.)
2. **Use custom input** for specific times (9:15, 10:45)
3. **Toggle format** based on your preference

### Avoiding Errors
- Always set Start Time first
- End Time automatically filters invalid options
- Red validation messages show issues clearly

### Consistency
- Use same format across all sessions
- Stick to hourly presets when possible
- Round to :00 or :30 for cleaner schedules

## Troubleshooting

### "Time must be at or after..." Message

**Cause:** End Time is before Start Time

**Fix:**
1. Update Start Time to earlier time
2. Or update End Time to later time
3. Validation message disappears when valid

### Can't See Desired Preset

**Cause:** Time is outside min/max constraints

**Fix:**
1. Adjust the other time field first
2. Or use custom time input
3. Check if time makes logical sense

### Dropdown Won't Open

**Cause:** Field is disabled during loading

**Fix:**
1. Wait for form to finish loading
2. Check if you have permission to edit
3. Refresh page if needed

### Time Shows Wrong Format

**Cause:** Format toggle set incorrectly

**Fix:**
1. Open dropdown
2. Click "12h" or "24h" button
3. Format changes immediately

## Examples

### Create Conference Schedule

**Day 1: Morning Sessions**
```
Registration:  8:00 AM - 9:00 AM
Opening:       9:00 AM - 10:00 AM
Worship:      10:00 AM - 11:00 AM
Break:        11:00 AM - 11:30 AM
Teaching:     11:30 AM - 1:00 PM
Lunch:         1:00 PM - 2:00 PM
```

**Using TimePicker:**
1. All times are available as presets except 11:30
2. Use custom input only for 11:30 AM
3. 5 out of 6 sessions created with presets
4. Total time: < 2 minutes for full schedule

### Weekly Service Times

**Regular Services:**
```
Sunday 1st:    9:00 AM - 11:00 AM
Sunday 2nd:    6:00 PM - 8:00 PM
Wednesday:     7:00 PM - 9:00 PM
```

**Using TimePicker:**
- All times available as presets
- Consistent hourly blocks
- No custom input needed

## Best Practices

### For Event Organizers

1. **Plan Time Blocks**
   - Use hourly increments when possible
   - Reserve :15 and :45 for special cases
   - Keep sessions consistent

2. **Set Realistic Durations**
   - Minimum 30 minutes per session
   - Include buffer time between sessions
   - Account for setup/teardown

3. **Use Validation**
   - Let the picker enforce logical times
   - Don't override validation errors
   - Check all sessions after creation

### For Administrators

1. **Create Templates**
   - Save common time patterns
   - Reuse successful schedules
   - Document your time standards

2. **Train Staff**
   - Show how to use presets
   - Explain validation rules
   - Demonstrate format toggle

3. **Monitor Usage**
   - Check for time entry errors
   - Identify training needs
   - Gather user feedback

## Support

### Need Help?

1. **Check Validation Messages**
   - Red text shows what's wrong
   - Fix the issue indicated
   - Message disappears when resolved

2. **Try Preset First**
   - Presets are guaranteed valid
   - Custom input allows more flexibility
   - Mix both as needed

3. **Ask for Assistance**
   - Contact conference administrator
   - Reference this guide
   - Report bugs to development team

### Report Issues

If you encounter problems:

1. **Note the Error**
   - What you were trying to do
   - What time values you entered
   - What error message appeared

2. **Check Browser**
   - Use latest Chrome, Firefox, or Safari
   - Clear cache if needed
   - Try different browser if issue persists

3. **Contact Support**
   - Include screenshots
   - Describe steps to reproduce
   - Mention browser and device type

## Changelog

### v1.0.0 (December 2025)
- Initial release
- 17 preset time slots
- 12/24 hour format toggle
- Min/max time validation
- Accessibility features
- Mobile optimization

---

**Last Updated:** December 7, 2025
**Component Version:** 1.0.0
**Applies To:** ChurchFlow Session Management
