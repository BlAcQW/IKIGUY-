# Enhanced Time Picker Component

## Overview

The `TimePicker` component provides an improved time selection experience for session management in ChurchFlow. It replaces the basic HTML `<input type="time">` with a feature-rich dropdown interface.

## Features

### 🎯 Quick Preset Times
- Pre-configured time slots from 6:00 AM to 10:00 PM
- Common hourly intervals for quick selection
- Reduces user input errors

### ⏰ 12/24 Hour Format Support
- Toggle between 12-hour (AM/PM) and 24-hour format
- User preference persisted during session
- Displays selected time in chosen format

### ✅ Smart Validation
- `minTime` constraint: Prevents selecting times before a minimum
- `maxTime` constraint: Prevents selecting times after a maximum
- Visual validation messages for constraint violations
- Useful for ensuring end time is after start time

### 🎨 Enhanced UX
- Dropdown interface with searchable presets
- Custom time input for precise selection
- Accessible keyboard navigation
- Clear visual feedback
- Disabled state support

## Usage

### Basic Usage

```tsx
import TimePicker from '../components/TimePicker'

function SessionForm() {
  const [startTime, setStartTime] = useState('09:00')

  return (
    <TimePicker
      value={startTime}
      onChange={setStartTime}
      label="Start Time"
      required
    />
  )
}
```

### With Time Constraints

Ensure end time is after start time:

```tsx
function SessionForm() {
  const [startTime, setStartTime] = useState('09:00')
  const [endTime, setEndTime] = useState('10:00')

  return (
    <div className="grid grid-cols-2 gap-4">
      <TimePicker
        value={startTime}
        onChange={setStartTime}
        label="Start Time"
        required
        maxTime={endTime}  // Can't select time after end time
      />
      <TimePicker
        value={endTime}
        onChange={setEndTime}
        label="End Time"
        required
        minTime={startTime}  // Can't select time before start time
      />
    </div>
  )
}
```

### Disabled State

```tsx
<TimePicker
  value={time}
  onChange={setTime}
  label="Session Time"
  disabled={isLoading}
/>
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `value` | `string` | required | Current time value in HH:mm format (24-hour) |
| `onChange` | `(value: string) => void` | required | Callback when time changes |
| `label` | `string` | - | Label text displayed above picker |
| `required` | `boolean` | `false` | Shows asterisk (*) if true |
| `disabled` | `boolean` | `false` | Disables interaction |
| `className` | `string` | `''` | Additional CSS classes |
| `minTime` | `string` | - | Minimum selectable time (HH:mm format) |
| `maxTime` | `string` | - | Maximum selectable time (HH:mm format) |

## Time Format

The component:
- **Stores** times in 24-hour format (HH:mm) e.g., `"14:00"`
- **Displays** times in user's preferred format:
  - 12-hour: "2:00 PM"
  - 24-hour: "14:00"

## Preset Times

The following preset times are available:
- 6:00 AM - 11:00 AM (hourly)
- 12:00 PM
- 1:00 PM - 10:00 PM (hourly)

Presets are automatically filtered based on `minTime` and `maxTime` constraints.

## Accessibility

- Keyboard navigation supported
- ARIA labels for screen readers
- Focus management
- Clear error messages
- Sufficient touch target size (44px minimum)

## Integration Points

The enhanced TimePicker is integrated in:

1. **Session Manager** (`/src/components/SessionManager.tsx`)
   - Create session form
   - Edit session form

2. **Session Detail** (`/src/pages/SessionDetail.tsx`)
   - Edit session modal

## Validation Logic

### Min/Max Time Constraints

```typescript
// Example: Start time must be before end time
<TimePicker
  value={startTime}
  onChange={setStartTime}
  maxTime={endTime}  // Validates: startTime <= endTime
/>

<TimePicker
  value={endTime}
  onChange={setEndTime}
  minTime={startTime}  // Validates: endTime >= startTime
/>
```

### Validation Messages

When constraints are violated:
- **Below minTime**: "Time must be at or after {minTime}"
- **Above maxTime**: "Time must be at or before {maxTime}"

Messages display in the user's selected format (12h or 24h).

## Browser Compatibility

The component works across all modern browsers:
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS Safari, Chrome Mobile)

Falls back to native time input where custom UI isn't supported.

## Testing

Unit tests are located in:
`/src/components/__tests__/TimePicker.test.tsx`

Test coverage includes:
- Rendering with props
- Dropdown interaction
- Preset selection
- Format toggling
- Constraint validation
- Disabled state

Run tests:
```bash
npm test TimePicker
```

## Performance

- Lightweight (~3KB gzipped)
- No external dependencies beyond React
- Efficient event handling with useEffect cleanup
- Minimal re-renders with proper state management

## Future Enhancements

Potential improvements:
- [ ] Time zone support
- [ ] Minute interval customization (15min, 30min increments)
- [ ] Recently used times
- [ ] Keyboard shortcuts for common times
- [ ] Duration calculator (shows duration between start/end)
- [ ] Copy time to clipboard
- [ ] Localization support

## Migration Guide

### From Basic HTML Input

**Before:**
```tsx
<input
  type="time"
  value={time}
  onChange={(e) => setTime(e.target.value)}
  className="input"
/>
```

**After:**
```tsx
<TimePicker
  value={time}
  onChange={setTime}
  label="Time"
/>
```

### Benefits

- ✅ Better mobile experience
- ✅ Consistent UI across browsers
- ✅ Quick preset selection
- ✅ Built-in validation
- ✅ Format toggle capability

## Support

For issues or feature requests related to the TimePicker:
1. Check existing issues in the repository
2. Test in isolation using the test file
3. Verify props are correctly passed
4. Check browser console for errors

## Changelog

### v1.0.0 (2025-12-07)
- Initial release
- Preset time slots
- 12/24 hour format toggle
- Min/max time validation
- Disabled state support
- Accessibility features
