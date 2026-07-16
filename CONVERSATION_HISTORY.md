# Conversation History Feature

## Overview

Added session-based conversation history with a split-button design for ESP selectors.

## Features

### 1. Split Button Design
- Each ESP button now splits into two sections:
  - **Main button**: Selects the ESP (left side)
  - **History button**: Opens conversation history (right side, with clock icon)
- Both buttons share the same rounded corners and orange active state
- Seamless visual integration with existing design

### 2. Per-ESP History
- Each ESP maintains its own conversation history
- Histories are stored separately:
  - Klaviyo conversations
  - DotDigital conversations
  - Other/Webhook conversations
- Switch between ESPs without losing conversation context

### 3. Session Storage
- History persists during the current browser session
- Survives page refreshes
- Cleared when browser session ends
- Stored in browser's `sessionStorage`

### 4. History Modal
- **Opens**: Click the clock icon next to any ESP
- **Shows**: All conversations for that ESP in chronological order
- **Displays**:
  - Timestamp for each conversation
  - User message (dark gradient background)
  - Assistant response (white background)
- **Empty State**: Shows helpful message when no history exists

### 5. Clear History
- Button at bottom of history modal
- Clears only the selected ESP's history
- Requires confirmation
- Cannot be undone

## How to Use

### View History
1. Select an ESP (Klaviyo, DotDigital, or Other/Webhook)
2. Have at least one conversation
3. Click the **clock icon** next to the ESP name
4. History modal opens with all conversations

### Clear History
1. Open history modal
2. Click **"Clear History"** button at bottom
3. Confirm the action
4. History is cleared for that ESP only

## Technical Details

### Storage Format
```javascript
{
  "klaviyo": [
    { role: "user", content: "...", timestamp: "2026-07-15T..." },
    { role: "assistant", content: "...", timestamp: "2026-07-15T..." }
  ],
  "dotdigital": [...],
  "other/webhook": [...]
}
```

### Session Storage Key
- `espConversationHistories`

### Conversation Grouping
- Messages are grouped in pairs (user + assistant)
- Each pair shows as one conversation block
- Chronological order (newest last)

## UI Components

### Split Button Structure
```html
<div class="esp-button-group active">
    <button class="esp-item active">Klaviyo</button>
    <button class="esp-history-btn">🕐</button>
</div>
```

### CSS Classes
- `.esp-button-group` - Container for split button
- `.esp-item` - Main ESP selector button
- `.esp-history-btn` - History icon button
- `.history-modal` - Modal container
- `.history-content` - Scrollable content area
- `.history-conversation` - Individual conversation block
- `.history-message` - User or assistant message

## Design Notes

### Colors
- Active state: Orange (#FDB768)
- User messages: Dark gradient
- Assistant messages: White with border
- Empty state: Gray icon with message

### Layout
- Split button: 70/30 ratio (ESP name / history icon)
- History button width: 42px fixed
- Modal max height: 85vh (scrollable)
- Rounded corners: 6px

## Future Enhancements

Potential additions:
- Export history as PDF/JSON
- Search within history
- Filter by date range
- Persistent storage (database)
- Share conversations
- Favorite/star important conversations

---

**Status**: ✅ Complete and functional  
**Storage**: Session-based (browser session)  
**Per ESP**: Separate history for each integration
