# Travel Planner - Quick Reference Card

## 🚀 Quick Start

### Access the Travel Planner
```
1. Navigate to: http://localhost/travel
2. Login with your account
3. Click "New Trip" to get started
```

---

## 📊 Features at a Glance

| Feature | What It Does | Where to Find It |
|---------|--------------|------------------|
| **Trip List** | View all your trips | `/travel` |
| **Create Trip** | Add new trip | Click "New Trip" button |
| **Trip Details** | View trip overview | Click trip card |
| **Gantt Chart** | Visual timeline | Trip Details → Timeline tab |
| **Map View** | Interactive map | Trip Details → Overview tab |
| **Add Activity** | Schedule activity | Click "Add Activity" button |
| **Add Accommodation** | Book lodging | Click "Add Accommodation" |
| **Weather** | View forecast | Sidebar on trip details |
| **Export Calendar** | Download .ics | Click "Add to Calendar" |

---

## 🎨 Core Components

### 1. Gantt Chart (Timeline Tab)
```javascript
✓ Drag activities to reschedule
✓ Click activity to edit
✓ Color-coded by category:
  - Blue: Sightseeing
  - Green: Dining
  - Yellow: Transport
  - Cyan: Entertainment
  - Gray: Shopping
  - Dark: Other
```

### 2. Interactive Map (Overview Tab)
```javascript
✓ Green markers = Accommodations
✓ Blue markers = Activities
✓ Click markers for details
✓ Auto-centers on locations
```

### 3. Activity Modal
```
13 Fields:
- Name, Category, Description
- Start/End Date & Time
- Location + Coordinates
- Priority, Cost, Duration
- Notes
```

### 4. Accommodation Modal
```
16 Fields:
- Name, Type, Address, City
- Coordinates, Phone, Website
- Check-in/out Date & Time
- Cost, Currency
- Confirmation #, Status
- Notes
```

---

## 🔗 API Endpoints

### Trips
```
GET    /api/travel/trips              List trips
POST   /api/travel/trips              Create trip
GET    /api/travel/trips/{id}         Get trip
PUT    /api/travel/trips/{id}         Update trip
DELETE /api/travel/trips/{id}         Delete trip
```

### Activities
```
GET    /api/travel/trips/{id}/activities          List
POST   /api/travel/trips/{id}/activities          Create
GET    /api/travel/trips/{id}/activities/{aid}    Get
PUT    /api/travel/trips/{id}/activities/{aid}    Update
DELETE /api/travel/trips/{id}/activities/{aid}    Delete
```

### Accommodations
```
GET    /api/travel/trips/{id}/accommodations          List
POST   /api/travel/trips/{id}/accommodations          Create
GET    /api/travel/trips/{id}/accommodations/{aid}    Get
PUT    /api/travel/trips/{id}/accommodations/{aid}    Update
DELETE /api/travel/trips/{id}/accommodations/{aid}    Delete
```

---

## 🎯 Common Tasks

### Create a Complete Trip
```
1. Click "New Trip"
2. Fill in:
   - Name: "Summer in Paris"
   - Destination: Paris, France
   - Dates: June 1-7, 2026
   - Budget: €2000
3. Click "Create Trip"
4. Add activities (3-5 recommended)
5. Add accommodation (hotel/Airbnb)
6. View timeline in Gantt chart
7. View locations on map
8. Export to calendar
```

### Add Activity with Map Marker
```
1. On trip detail page
2. Click "Add Activity"
3. Fill in basic info (name, category, dates)
4. Add location (address or coordinates)
5. To get coordinates:
   - Google Maps: Right-click location → Copy coordinates
   - Paste into Latitude/Longitude fields
6. Save
7. Check Overview tab → marker appears
```

### Reschedule Activity
```
Method 1 (Gantt):
1. Go to Timeline tab
2. Drag activity bar to new date
3. Dates auto-save

Method 2 (Modal):
1. Click activity in list or Gantt
2. Edit start/end dates
3. Click "Save Activity"
```

---

## 🛠️ Troubleshooting

### Map Not Loading
```
✓ Check browser console for errors
✓ Verify Leaflet.js CDN is accessible
✓ Check if trip has city/country set
✓ Try refreshing the page
```

### Gantt Chart Empty
```
✓ Add activities with dates first
✓ Ensure activities have start and end dates
✓ Switch to Timeline tab to trigger load
✓ Check browser console for errors
```

### Weather Not Showing
```
✓ Ensure trip has city and country
✓ Check weather API is running
✓ Refresh the page
✓ Check browser console for errors
```

### Modal Not Opening
```
✓ Ensure Bootstrap 5 is loaded
✓ Check browser console for errors
✓ Refresh the page
✓ Clear browser cache
```

---

## 📱 Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `ESC` | Close modal |
| `Enter` | Submit form (when focused) |
| `Tab` | Navigate form fields |
| `Click + Drag` | Move activity in Gantt |

---

## 🎨 Category Colors

| Category | Color | Hex |
|----------|-------|-----|
| Sightseeing | Blue | #0d6efd |
| Dining | Green | #198754 |
| Transport | Yellow | #ffc107 |
| Entertainment | Cyan | #0dcaf0 |
| Shopping | Gray | #6c757d |
| Other | Dark | #212529 |

---

## 🌍 Supported Currencies
- EUR (€)
- USD ($)
- GBP (£)
- JPY (¥)
- AUD (A$)
- CAD (C$)
- CHF (Fr)

---

## ⏰ Common Timezones
- America/New_York (EST/EDT)
- America/Los_Angeles (PST/PDT)
- Europe/London (GMT/BST)
- Europe/Paris (CET/CEST)
- Asia/Tokyo (JST)
- Australia/Sydney (AEST/AEDT)
- And 25+ more...

---

## 🔒 Permissions

| Action | Required Permission |
|--------|---------------------|
| View own trips | Logged in |
| Create trip | Logged in |
| Edit own trip | Trip owner |
| Delete own trip | Trip owner |
| Export calendar | Trip owner |

---

## 📊 Data Limits

| Item | Limit |
|------|-------|
| Trips per user | Unlimited |
| Activities per trip | Unlimited |
| Accommodations per trip | Unlimited |
| Trip name length | 255 characters |
| Description length | Text (unlimited) |
| Notes length | Text (unlimited) |

---

## 🚀 Performance Tips

1. **Lazy Loading**: Tabs load content only when activated
2. **Auto-refresh**: Changes update views automatically
3. **Caching**: Map tiles cached by browser
4. **Batch Operations**: Use modals for multiple changes
5. **Pagination**: Trip list paginated (10 per page)

---

## 📞 Quick Help

### Getting Started Issues?
1. Make sure you're logged in
2. Check you have the latest browser version
3. Clear browser cache if seeing old version
4. Check browser console for errors (F12)

### Data Not Saving?
1. Check form validation (required fields)
2. Verify authentication cookie is set
3. Check API is running (http://localhost:8000)
4. Check database is accessible

### Visual Issues?
1. Hard refresh (Ctrl+F5 or Cmd+Shift+R)
2. Check Bootstrap 5 CSS is loaded
3. Check Font Awesome icons loaded
4. Try different browser

---

## 📚 Documentation Links

- **Overview**: `/docs/travel-planner/01_OVERVIEW.md`
- **Database**: `/docs/travel-planner/02_DATABASE_SCHEMA.md`
- **API Docs**: `/docs/travel-planner/03_API_ENDPOINTS.md`
- **Pages**: `/docs/travel-planner/04_FRONTEND_PAGES.md`
- **Gantt/Maps**: `/docs/travel-planner/GANTT_AND_MAPS_COMPLETE.md`
- **Phase 3**: `/docs/travel-planner/PHASE_3_COMPLETE.md`

---

## 🎉 Happy Traveling!

**Built with:** Flask, PostgreSQL, Bootstrap 5, Leaflet.js, Frappe Gantt  
**Version:** 1.0  
**Last Updated:** October 25, 2025
