# Quick Start Guide - New UI Features

## What's New? 🎉

Your Strategic Tanker Tracker now has:
- ✅ **Better UI** with modern gradient header and improved layout
- ✅ **Advanced Filters** to focus on specific vessels
- ✅ **Smaller Icons** for a cleaner, less cluttered map
- ✅ **Interactive Legend** showing what each color means
- ✅ **Responsive Design** that works on phones and tablets

---

## 🎨 Visual Changes

### Top Header Panel
```
┌─────────────────────────────────────────┐
│ 🛢️ Tracker │ Active: 2683 │ 🔍 Filters │
│            │ Tankers: 39  │ ⏸ Pause   │
└─────────────────────────────────────────┘
```

### Map Colors (New Scheme)
- 🔴 **Red** = Oil Tankers (strategic focus)
- 🔵 **Blue** = Cargo Ships
- 🟢 **Green** = Other Vessels
- 🔲 **Light Blue** = Port Terminals

### Smaller Markers
Map icons are now **50% smaller** → easier to see patterns across the map

---

## 🔍 How to Use Filters

### Step 1: Open Filters
Click the **🔍 Filters** button in the top right corner
- Or press `Ctrl+F` on your keyboard

### Step 2: Choose What to Show
Select or deselect options:
- **Vessel Type**: Tankers, Cargo, Other
- **Speed**: Moving or Stationary
- **Status**: Under Way or Anchored  
- **Size**: Large, Medium, Small

### Step 3: Apply
Click the **Apply** button
- Wait for refresh to see changes
- Or click **Refresh Now** button to speed it up

### Step 4: Reset
Click **Reset** to show everything again
- Filter preferences are saved automatically

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+F` | Toggle filter panel |
| `Space` | Pause / Resume auto-refresh |
| `Ctrl+R` | Manual refresh |

---

## 📊 Reading the Dashboard

### Top Left Stats
- **Active Vessels**: Total number being tracked
- **Tankers**: Count of oil tankers (red color)
- **Live Tracking**: Status indicator (green dot = active)

### Bottom Right Legend
Visual guide showing what each color represents on the map

---

## 💡 Tips & Tricks

### Find Tankers Only
1. Click **🔍 Filters**
2. Uncheck "Cargo Ships" and "Other Vessels"
3. Check only "Oil Tankers"
4. Click **Apply**
5. Click **Refresh Now**

### See Stationary Vessels
1. Click **🔍 Filters**
2. Uncheck "Moving" (> 0.5 knots)
3. Keep "Stationary" checked
4. Click **Apply**

### Focus on Large Ships
1. Click **🔍 Filters**
2. Uncheck "Medium" and "Small"
3. Check only "Large (> 100k tons)"
4. Click **Apply**

### Mobile Friendly
On phones/tablets:
- Tap **🔍 Filters** to see options (slides from left)
- Tap again to hide and see more map
- Portrait or landscape both work well

---

## 🎯 Common Scenarios

### "I want to monitor all tankers in transit"
✓ Filter: Tankers + Moving + Under Way + Large

### "Show me ships currently anchored"
✓ Filter: All types + Stationary + Anchored

### "Which cargo ships are near me?"
✓ Filter: Cargo Ships only + Moving

### "Find potential ports/terminals"
✓ Look for blue dots in the legend area

---

## ⚙️ Settings & Auto-Refresh

### Pause Updates
Click **⏸ Pause** button to stop auto-refreshing
- Good for studying a particular view
- Click **Resume** to restart updates

### Manual Refresh
Click **🔄 Refresh** to update immediately
- Don't wait for auto-refresh cycle
- Useful when expecting new data

### Auto-Refresh Timer
Shows countdown in top right:
- Counts down from 30 seconds (default)
- Pauses when you interact with map
- Resets when page regains focus

---

## 🐛 Troubleshooting

### Filters Not Working?
1. Try clicking **Apply** again
2. Refresh page with F5
3. Clear browser cache (Ctrl+Shift+Delete)

### Map Not Updating?
1. Check internet connection
2. Click **🔄 Refresh** button
3. Check if **⏸ Pause** is on
4. Close other browser tabs

### Icons Look Wrong?
1. Zoom in/out on map
2. Refresh page (F5)
3. Try different browser

### Performance Slow?
1. Reduce zoom level (zoom out)
2. Apply filters to show fewer vessels
3. Close other applications
4. Check browser memory (Dev Tools → Performance)

---

## 📱 Device Compatibility

### Desktop / Laptop ✅
- Full features
- All controls visible
- Best experience

### Tablet ✅
- Landscape: Full panel visible
- Portrait: Panel slides in from side
- Touch-friendly buttons

### Mobile Phone ✅
- Vertical layout
- Swipe to access filters
- Large buttons for easy tapping

---

## 🚀 Pro Tips

1. **Combine Filters**: Use multiple filters together for precise results
2. **Save Preferences**: Filters auto-save in browser
3. **Keyboard Power User**: Use Ctrl+F to quickly toggle filters
4. **Zoom Smart**: Zoom in on regions to see details, zoom out for big picture
5. **Read Popups**: Click any marker to see detailed vessel info

---

## ❓ FAQ

**Q: Do filters affect the data collected?**  
A: No, they only hide/show markers. Full data still updates in background.

**Q: Why are some ships missing?**  
A: Filters might be hiding them. Click Reset to show all.

**Q: Can I export the filtered data?**  
A: Future feature planned! For now, take screenshots.

**Q: How often does data update?**  
A: Every 30 seconds (default, configurable)

**Q: What's the red indicator?**  
A: Shows application is actively receiving live vessel data

---

## 📞 Need Help?

Check these files for more info:
- `README.md` - Full documentation
- `UI_IMPROVEMENTS.md` - Technical details
- `config.py` - Settings and customization

---

**Happy Tracking! 🌍⛴️**




