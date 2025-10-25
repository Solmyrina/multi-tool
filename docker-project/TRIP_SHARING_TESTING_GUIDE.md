# Trip Sharing System - Testing Guide

## Quick Start Testing

### Prerequisites
- At least 2 user accounts created
- At least 1 trip created by the first user

---

## Test Scenario 1: Share a Trip

**As Trip Owner (User A)**:

1. **Navigate to trip detail page**
   - Go to "My Trips"
   - Click on any trip

2. **Open sharing modal**
   - Click "Share Trip" button in header
   - Modal should open with user search

3. **Search for user**
   - Type User B's email or username
   - Search results should appear after 300ms
   - Click on User B's name

4. **Select role**
   - Choose "Editor" from dropdown
   - Click "Share"
   - User B should appear in shares list with role badge

5. **Edit permissions (optional)**
   - Click "Permissions" button next to User B
   - Permission editor modal opens
   - Uncheck "Budget > Read" permission
   - Click "Save Permissions"
   - Toast: "Permissions updated successfully"

---

## Test Scenario 2: Access Shared Trip

**As Shared User (User B)**:

1. **View shared trip in list**
   - Go to "My Trips"
   - Should see trip with "Shared" badge
   - Owner name shown: "Owner: UserA"

2. **Open shared trip**
   - Click on shared trip
   - Trip detail page loads

3. **Verify read access**
   - Can view all activities, accommodations, routes
   - Can see trip details

4. **Verify budget hiding** (if budget read = false):
   - No cost fields visible in activity/accommodation cards
   - No "Budget" tab
   - No expenses visible
   - No cost inputs in forms

5. **Verify write permissions** (Editor role):
   - Can see "Add Activity" button
   - Can see "Add Accommodation" button
   - Can see edit buttons on cards
   - Cannot see "Edit Trip" or "Delete Trip" buttons (owner only)

6. **Try to add activity**:
   - Click "Add Activity"
   - Fill in form (cost field should be hidden if no budget permission)
   - Save successfully

7. **Try to edit activity**:
   - Click edit button on activity card
   - Modify details
   - Save successfully

8. **Try to edit trip details** (should fail):
   - "Edit Trip" button should not be visible
   - Direct API call would return 403

---

## Test Scenario 3: Viewer Role

**As Trip Owner**:

1. Share trip with User C with "Viewer" role

**As User C**:

1. Open shared trip
2. Verify restrictions:
   - ✅ Can view all data
   - ❌ No "Add Activity" button
   - ❌ No "Add Accommodation" button
   - ❌ No edit buttons on cards
   - ❌ No delete buttons on cards
   - ❌ Clicking edit function shows toast: "No permission to edit activities"

---

## Test Scenario 4: Admin Role

**As Trip Owner**:

1. Share trip with User D with "Admin" role

**As User D**:

1. Open shared trip
2. Verify full access:
   - ✅ Can add activities, accommodations, routes
   - ✅ Can edit all items
   - ✅ Can delete items
   - ✅ Can manage budget/expenses
   - ❌ Cannot delete trip itself (owner only)

---

## Test Scenario 5: Permission Hierarchy

**As Trip Owner**:

1. Click "Permissions" on a share
2. Try to enable "Delete" without "Write":
   - Check "Activities > Delete"
   - "Write" should auto-check
   - "Read" should auto-check

3. Try to disable "Read" when "Write" is enabled:
   - Uncheck "Activities > Read"
   - "Write" should auto-uncheck
   - "Delete" should auto-uncheck

---

## Test Scenario 6: Revoke Access

**As Trip Owner**:

1. Click "Revoke" button on a share
2. Confirm deletion
3. Toast: "Access revoked successfully"
4. User removed from shares list

**As Revoked User**:

1. Refresh trip list
2. Trip should no longer appear in list
3. Direct access to trip URL should return 404

---

## Test Scenario 7: Budget Permission Edge Cases

**Setup**: Share trip with budget read=false, budget write=false

**Expected Behavior**:
1. In trip list:
   - No "Spent" stat visible (or shows 0)
   - No budget progress bar

2. In trip detail:
   - No cost displays on activity cards
   - No cost inputs in activity form
   - No cost displays on accommodation cards
   - No cost inputs in accommodation form
   - No "Budget" tab
   - GET /expenses returns empty array
   - No "Add Expense" button

**Setup**: Enable budget read=true, keep write=false

**Expected Behavior**:
1. Can see costs everywhere
2. Cannot add/edit expenses
3. No "Add Expense" button
4. Cost inputs disabled/hidden in forms

---

## API Testing (Using curl or Postman)

### 1. Share Trip
```bash
curl -X POST http://localhost/api/travel/trips/1/shares \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "role": "editor"}' \
  --cookie "session=YOUR_SESSION"
```

Expected: 200, share created

### 2. Get Shares
```bash
curl http://localhost/api/travel/trips/1/shares \
  --cookie "session=YOUR_SESSION"
```

Expected: List of shares with permissions

### 3. Update Permissions
```bash
curl -X PUT http://localhost/api/travel/trips/1/shares/1 \
  -H "Content-Type: application/json" \
  -d '{
    "permissions": [
      {"category": "budget", "can_read": true, "can_write": false, "can_delete": false}
    ]
  }' \
  --cookie "session=YOUR_SESSION"
```

Expected: 200, permissions updated

### 4. Revoke Access
```bash
curl -X DELETE http://localhost/api/travel/trips/1/shares/1 \
  --cookie "session=YOUR_SESSION"
```

Expected: 200, access revoked

### 5. Access Shared Trip (as shared user)
```bash
curl http://localhost/api/travel/trips/1 \
  --cookie "session=SHARED_USER_SESSION"
```

Expected: 200, trip data with permissions object

### 6. Try Unauthorized Action
```bash
# As viewer, try to delete activity
curl -X DELETE http://localhost/api/travel/trips/1/activities/5 \
  --cookie "session=VIEWER_SESSION"
```

Expected: 403, "No permission to delete activities"

---

## Database Verification

### Check Shares
```sql
SELECT ts.*, u.email, u.username 
FROM trip_shares ts
JOIN users u ON ts.shared_with_user_id = u.id
WHERE trip_id = 1;
```

### Check Permissions
```sql
SELECT tp.*, ts.shared_with_user_id 
FROM trip_permissions tp
JOIN trip_shares ts ON tp.share_id = ts.id
WHERE ts.trip_id = 1;
```

### Check Permission View
```sql
SELECT * FROM trip_user_permissions 
WHERE trip_id = 1 AND user_id = 'USER_UUID';
```

---

## Common Issues & Solutions

### Issue: "Trip not found" when accessing shared trip
**Solution**: Check trip_shares table, ensure share exists and user_id is correct

### Issue: Budget data still visible when permission disabled
**Solution**: Clear browser cache, check API response (should not contain cost fields)

### Issue: Edit button visible but action fails
**Solution**: Check console for permission error, verify hasPermission() function loaded

### Issue: Permission checkboxes not enforcing hierarchy
**Solution**: Check browser console for JavaScript errors, verify enforcePermissionHierarchy() function

### Issue: User search returns no results
**Solution**: 
- Check user exists in database
- Verify email/username is correct
- Check API endpoint: /api/travel/users/search?q=...

---

## Success Criteria

✅ All 7 test scenarios pass
✅ No JavaScript errors in console
✅ No 500 errors from API
✅ Budget data properly hidden
✅ Buttons properly hidden based on permissions
✅ Permission hierarchy enforced
✅ Toast notifications appear for all actions
✅ Database constraints prevent invalid data

---

## Performance Testing

### Test with Multiple Shares:
1. Share same trip with 10 users
2. Page load time should remain < 2 seconds
3. Permission checks should not cause noticeable delay

### Test with Multiple Trips:
1. Create 20 trips
2. Share 10 of them with User B
3. User B's trip list should show all 10 shared trips
4. Load time should remain acceptable

---

## Security Testing

### Attempt Unauthorized Actions:
1. **Without login**: Try to access API → 401
2. **As non-shared user**: Try to access trip → 404
3. **As viewer**: Try to edit → 403
4. **SQL injection**: Try `' OR '1'='1` in search → Should be safe (parameterized)
5. **XSS**: Try `<script>alert('xss')</script>` in trip name → Should be escaped

---

## Regression Testing

After any code changes, verify:
1. Owner can still do everything
2. Shared trips still accessible
3. Permissions still enforced
4. Budget hiding still works
5. UI controls still hide/show correctly

---

**Last Updated**: October 25, 2025
**Status**: Ready for Testing
