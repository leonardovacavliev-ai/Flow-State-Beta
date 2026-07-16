# Sparkline Graphs Feature

## Overview

Each KPI card in the Usage Analytics dashboard now includes an integrated sparkline graph that visualizes the trend over time. The sparklines are compact, interactive, and provide instant visual feedback about metric performance.

## Features

### Visual Design
- **Mini line chart** integrated into the right side of each KPI card
- **Gradient fill** underneath the line for visual emphasis
- **Responsive sizing** - adapts to card width without making cards larger
- **High-DPI support** - crisp rendering on retina displays
- **Primary color theme** - matches app's design system (oklch(0.205 0 0))

### Interactive Tooltips
- **Hover to reveal** - Move mouse over sparkline to see details
- **Exact values** - Shows precise metric value for each date point
- **Date display** - Formatted as "MMM DD" (e.g., "Jan 15")
- **Unit labels** - Each tooltip includes the appropriate unit:
  - Sessions: "Sessions"
  - Users: "Users"
  - Avg Messages: "Avg Messages"
  - Feedback: "Feedback"
  - Session Time: "Seconds"
  - Message Length: "Characters"

### Visual Feedback on Hover
- **Highlighted data point** - 3px dot appears at cursor position
- **Vertical guide line** - Dashed line shows exact x-position
- **Smooth animations** - Fade in/out transitions
- **No flickering** - Efficient redraw logic

## Data Display Logic

### Time Ranges
- **Last 7 Days**: Shows all 7 daily data points
- **Last 90 Days**: Shows last 30 days (for readability)
- **All Time**: No sparkline shown (too much data to be meaningful)

### Data Source
Backend provides daily aggregated data via the `sparkline` field in analytics response:

```json
{
  "sparkline": {
    "dates": ["2026-07-08", "2026-07-09", ...],
    "sessions": [45, 52, 38, ...],
    "unique_users": [32, 41, 29, ...],
    "avg_messages": [3.2, 4.1, 2.8, ...],
    "feedback": [2, 1, 3, ...],
    "session_time": [245.3, 312.1, 189.4, ...],
    "msg_length": [142.5, 158.3, 135.2, ...]
  }
}
```

## Technical Implementation

### Canvas-Based Rendering
- Uses HTML5 Canvas for performance
- 50px height (fixed, doesn't increase card size)
- Dynamic width based on available space
- Scales for device pixel ratio (retina support)

### Calculation Logic
1. **Normalize data** - Scale values to fit canvas height with 10% padding
2. **Calculate points** - Map each data point to x,y coordinates
3. **Draw line** - Smooth line connecting all points
4. **Fill gradient** - Semi-transparent fill under the line
5. **Handle hover** - Real-time tooltip positioning and redrawing

### Tooltip Positioning
```javascript
// Positioned above the sparkline
tooltip.style.left = `${pointX}px`;
tooltip.style.top = `${canvasTop - 10}px`;
tooltip.style.transform = 'translate(-50%, -100%)';
```

### Performance Optimizations
- **Canvas caching** - Only redraws on hover
- **Event debouncing** - Efficient mousemove handling
- **Minimal DOM manipulation** - Tooltip reuses single element
- **Smart scaling** - Retina display optimization

## Browser Compatibility

Works in all modern browsers with Canvas support:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Accessibility

- Sparklines are visual enhancements, not required for understanding data
- Primary metric values are still clearly displayed
- Tooltips provide precise values for screen readers
- High contrast colors for visibility

## CSS Classes

```css
.sparkline-tooltip {
    /* Dark tooltip with white text */
    background: oklch(0.145 0 0);
    color: oklch(0.985 0 0);
    /* Smooth fade animations */
    transition: opacity 0.2s ease;
}

.sparkline-tooltip.visible {
    opacity: 1;
}
```

## Example Use Cases

### Trend Analysis
"Sessions are up 15% this week, but the sparkline shows a dip on Thursday - what happened that day?"

### Anomaly Detection
"Feedback count shows a spike on July 10th - hover to see it was 8 tickets that day."

### Pattern Recognition
"Average session time has a weekly pattern - weekends are consistently lower."

### Performance Validation
"The percentage shows +22%, and the sparkline confirms steady growth over the period."

## Future Enhancements

Potential improvements:
- **Multiple lines** - Compare current vs previous period
- **Annotations** - Mark specific events on the timeline
- **Zoom controls** - Click to expand sparkline to full chart
- **Export** - Download sparkline as PNG
- **Threshold lines** - Show goal/target lines
- **Color coding** - Green for up trends, red for down trends
- **Touch support** - Tap to show tooltip on mobile

## Maintenance

### Updating Colors
To match your brand colors, update in `app.js`:

```javascript
// Line color
ctx.strokeStyle = 'oklch(0.205 0 0)';  // Change this

// Fill gradient
ctx.fillStyle = 'oklch(0.205 0 0 / 0.1)';  // And this
```

### Adjusting Height
To make sparklines taller/shorter, change in `index.html`:

```html
<canvas id="sparkline-sessions" class="w-full" height="50"></canvas>
<!-- Change height="50" to desired value -->
```

### Adding New Sparklines
When adding a new KPI card with sparkline:

1. Add canvas element:
```html
<canvas id="sparkline-new-metric" class="w-full" height="50"></canvas>
```

2. Update backend to include data in sparkline object

3. Add render call in `loadAnalytics()`:
```javascript
renderSparkline('sparkline-new-metric', data.sparkline.new_metric, data.sparkline.dates, 'Units');
```

## Troubleshooting

### Sparklines not showing
- Check browser console for errors
- Verify backend returns sparkline data
- Ensure time range is not "All Time"
- Check canvas dimensions are non-zero

### Tooltip not appearing
- Verify tooltip element is created
- Check CSS classes are applied
- Inspect tooltip positioning values
- Ensure mousemove event is firing

### Blurry rendering
- Check device pixel ratio scaling
- Verify canvas width/height vs CSS size
- Ensure proper dpr multiplication

### Performance issues
- Reduce number of data points
- Debounce mousemove events
- Use requestAnimationFrame for redraws
- Consider web workers for calculations

## Code Reference

**Backend**: `backend/analytics.py` - Lines ~270-290 (sparkline data generation)

**Frontend HTML**: `frontend/index.html` - KPI card structure with canvas elements

**Frontend JS**: `frontend/app.js` - `renderSparkline()` function (main implementation)

**CSS**: `frontend/index.html` - `.sparkline-tooltip` styles
