# Admin Event Deletion - UI Guide

## 🎨 User Interface Overview

### Event Organizer Dashboard

The Event Organizer page displays all events created by the logged-in admin. Each event card has action buttons including the new **Delete** button.

```
┌─────────────────────────────────────────────────────────────┐
│  Event Organizer Dashboard                                  │
│  Create events, upload photos, and manage your portfolio    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Create New Event                                           │
│  [Event Name] [Location] [Date] [Category] [Thumbnail]     │
│  [Create Event Button]                                      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  My Events                                    [Refresh]     │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ [Event Img]  │  │ [Event Img]  │  │ [Event Img]  │    │
│  │              │  │              │  │              │    │
│  │ Summer Fest  │  │ Tech Conf    │  │ Wedding 2024 │    │
│  │ NYC          │  │ SF           │  │ LA           │    │
│  │ 2024-07-15   │  │ 2024-08-20   │  │ 2024-09-10   │    │
│  │ Festival     │  │ Conference   │  │ Wedding      │    │
│  │              │  │              │  │              │    │
│  │ 150 photos   │  │ 75 photos    │  │ 200 photos   │    │
│  │              │  │              │  │              │    │
│  │ [Edit]       │  │ [Edit]       │  │ [Edit]       │    │
│  │ [QR Code]    │  │ [QR Code]    │  │ [QR Code]    │    │
│  │ [View Photos]│  │ [View Photos]│  │ [View Photos]│    │
│  │ [Upload]     │  │ [Upload]     │  │ [Upload]     │    │
│  │ [Delete] ❌  │  │ [Delete] ❌  │  │ [Delete] ❌  │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## 🔴 Delete Button

### Location
- Bottom of each event card
- Red background color for visibility
- Labeled "Delete"

### Visual Style
```css
.btn-danger {
    background: #6b7280;  /* Gray background */
    color: white;
    padding: 10px 18px;
    border-radius: 8px;
    cursor: pointer;
}

.btn-danger:hover {
    opacity: 0.9;
    transform: translateY(-1px);
}
```

## 💬 Confirmation Modal

When the Delete button is clicked, a confirmation modal appears:

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  ┌───────────────────────────────────────────────────┐    │
│  │  Delete Event                                  ✕  │    │
│  ├───────────────────────────────────────────────────┤    │
│  │                                                   │    │
│  │  Are you sure you want to delete this event?     │    │
│  │  This action cannot be undone.                   │    │
│  │                                                   │    │
│  │                                                   │    │
│  │                    [Cancel]  [Delete Event]      │    │
│  │                                                   │    │
│  └───────────────────────────────────────────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Modal Features
- **Title:** "Delete Event"
- **Message:** Warning about permanent deletion
- **Close Button (✕):** Top-right corner
- **Cancel Button:** Gray, closes modal without action
- **Delete Event Button:** Red, confirms deletion

## 🎬 User Flow Animation

### Step 1: Initial State
```
Event Card
┌──────────────┐
│ Summer Fest  │
│ NYC          │
│ 150 photos   │
│              │
│ [Edit]       │
│ [QR Code]    │
│ [View Photos]│
│ [Upload]     │
│ [Delete] ❌  │ ← User hovers here
└──────────────┘
```

### Step 2: Click Delete
```
Modal Appears
┌─────────────────────────────┐
│  Delete Event            ✕  │
├─────────────────────────────┤
│                             │
│  Are you sure you want to   │
│  delete this event?         │
│  This action cannot be      │
│  undone.                    │
│                             │
│        [Cancel] [Delete]    │ ← User clicks Delete
└─────────────────────────────┘
```

### Step 3: Processing
```
Loading State
┌─────────────────────────────┐
│  Deleting event...          │
│  ⏳                         │
└─────────────────────────────┘
```

### Step 4: Success
```
Success Alert
┌─────────────────────────────────────┐
│ ✅ Event deleted successfully!      │
└─────────────────────────────────────┘

Event Card Disappears
┌──────────────┐  ┌──────────────┐
│ Tech Conf    │  │ Wedding 2024 │
│ SF           │  │ LA           │
│ 75 photos    │  │ 200 photos   │
└──────────────┘  └──────────────┘
```

## 🎨 Color Scheme

### Delete Button
- **Normal:** Gray (#6b7280)
- **Hover:** Slightly darker with lift effect
- **Active:** Pressed state

### Confirmation Modal
- **Background:** White (#ffffff)
- **Overlay:** Dark semi-transparent (rgba(0,0,0,0.6))
- **Border:** Rounded (15px)
- **Shadow:** Soft shadow for depth

### Alerts
- **Success:** Green background (#d1fae5), dark green text (#065f46)
- **Error:** Red background (#fee2e2), dark red text (#991b1b)

## 📱 Responsive Design

### Desktop (> 768px)
```
┌────────────┐ ┌────────────┐ ┌────────────┐
│  Event 1   │ │  Event 2   │ │  Event 3   │
│  [Delete]  │ │  [Delete]  │ │  [Delete]  │
└────────────┘ └────────────┘ └────────────┘
```

### Mobile (< 768px)
```
┌────────────┐
│  Event 1   │
│  [Delete]  │
└────────────┘

┌────────────┐
│  Event 2   │
│  [Delete]  │
└────────────┘

┌────────────┐
│  Event 3   │
│  [Delete]  │
└────────────┘
```

## 🔔 Notifications

### Success Message
```
┌─────────────────────────────────────────────┐
│ ✅ Event deleted successfully!              │
└─────────────────────────────────────────────┘
```
- Appears at top of page
- Green background
- Auto-dismisses after 5 seconds

### Error Messages
```
┌─────────────────────────────────────────────┐
│ ❌ Failed to delete event: [error reason]   │
└─────────────────────────────────────────────┘
```
- Appears at top of page
- Red background
- Auto-dismisses after 5 seconds

### Possible Error Messages
1. "Unauthorized" - Not logged in as admin
2. "Event not found" - Event doesn't exist
3. "You can only delete events you created" - Wrong owner
4. "Failed to delete event" - Server error

## 🎯 Accessibility

### Keyboard Navigation
- **Tab:** Navigate to Delete button
- **Enter/Space:** Activate Delete button
- **Escape:** Close modal without deleting

### Screen Readers
- Delete button has clear label: "Delete"
- Modal has descriptive title: "Delete Event"
- Confirmation message is read aloud
- Success/error alerts are announced

### Visual Indicators
- Red color for destructive action
- Warning icon in modal
- Clear confirmation message
- Hover effects for interactivity

## 🖱️ Mouse Interactions

### Delete Button
- **Hover:** Button lifts slightly, opacity changes
- **Click:** Opens confirmation modal
- **Cursor:** Changes to pointer

### Modal
- **Click outside:** Closes modal (no deletion)
- **Click ✕:** Closes modal (no deletion)
- **Click Cancel:** Closes modal (no deletion)
- **Click Delete Event:** Confirms deletion

## 📊 State Management

### JavaScript Variables
```javascript
let eventToDelete = null;  // Stores event being deleted

// Set when Delete clicked
eventToDelete = {
    id: "event_abc123",
    name: "Summer Fest"
};

// Cleared after deletion or cancel
eventToDelete = null;
```

### Modal States
1. **Hidden:** `display: none`
2. **Visible:** `display: block`
3. **Processing:** Loading indicator
4. **Success:** Auto-close after 2 seconds
5. **Error:** Show error message

## 🔄 Refresh Behavior

After successful deletion:
1. Modal closes automatically
2. Success alert appears
3. Event list refreshes via `loadMyEvents()`
4. Deleted event card disappears
5. Remaining events re-arrange

## 💡 Best Practices

### User Experience
- ✅ Clear warning about permanent deletion
- ✅ Two-step confirmation (click + modal)
- ✅ Visual feedback (colors, animations)
- ✅ Success/error notifications
- ✅ Automatic list refresh

### Visual Design
- ✅ Red color for destructive action
- ✅ Consistent button styling
- ✅ Smooth animations
- ✅ Clear typography
- ✅ Adequate spacing

### Accessibility
- ✅ Keyboard navigation
- ✅ Screen reader support
- ✅ Focus indicators
- ✅ Clear labels
- ✅ Color contrast

---

*UI Guide created: December 13, 2024*
