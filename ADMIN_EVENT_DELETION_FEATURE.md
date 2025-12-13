# Admin Event Deletion Feature

## Overview
This feature allows administrators to delete events they have created, including all associated data (photos, folders, and metadata).

## Implementation Date
December 13, 2024

## Changes Made

### Backend Changes

#### New API Endpoint: `DELETE /api/delete_event/<event_id>`

**Location:** `backend/app.py` (after `update_event_thumbnail` function)

**Authentication:** Requires admin authentication

**Authorization:** Admin can only delete events they created (ownership validation)

**Functionality:**
1. Validates admin authentication
2. Loads events data from `events_data.json`
3. Finds the target event
4. Validates ownership (admin can only delete their own events)
5. Deletes associated folders:
   - `uploads/<event_id>/` - Original uploaded photos
   - `processed/<event_id>/` - Processed and organized photos
6. Removes event from `events_data.json`
7. Returns success/error response

**Request:**
```http
DELETE /api/delete_event/event_abc123
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Event deleted successfully"
}
```

**Response (Unauthorized):**
```json
{
  "success": false,
  "error": "Unauthorized"
}
```
Status: 401

**Response (Not Found):**
```json
{
  "success": false,
  "error": "Event not found"
}
```
Status: 404

**Response (Forbidden):**
```json
{
  "success": false,
  "error": "You can only delete events you created"
}
```
Status: 403

**Response (Server Error):**
```json
{
  "success": false,
  "error": "Failed to delete event"
}
```
Status: 500

### Frontend Changes

**Location:** `frontend/pages/event_organizer.html`

The frontend already had the delete button and confirmation modal implemented. The changes connect it to the new backend endpoint.

**UI Components:**
1. **Delete Button** - Red "Delete" button on each event card
2. **Confirmation Modal** - Asks user to confirm deletion
3. **JavaScript Functions:**
   - `showDeleteConfirm(eventId, eventName)` - Shows confirmation modal
   - `confirmDelete()` - Sends DELETE request to backend
   - Displays success/error alerts
   - Refreshes event list after successful deletion

**User Flow:**
1. Admin clicks "Delete" button on event card
2. Confirmation modal appears: "Are you sure you want to delete this event? This action cannot be undone."
3. Admin clicks "Delete Event" to confirm or "Cancel" to abort
4. If confirmed, DELETE request is sent to `/api/delete_event/<event_id>`
5. Success message displayed and event list refreshed
6. Event card disappears from the dashboard

### Testing

**Test File:** `backend/test_event_deletion.py`

**Test Cases:**
1. ✅ `test_delete_event_unauthorized` - Unauthenticated users cannot delete
2. ✅ `test_delete_event_not_found` - Returns 404 for non-existent events
3. ✅ `test_delete_event_wrong_owner` - Admin cannot delete other admin's events
4. ✅ `test_delete_event_success` - Successful deletion removes all data
5. ✅ `test_delete_event_missing_folders` - Handles missing folders gracefully

**Run Tests:**
```bash
cd backend
pytest test_event_deletion.py -v
```

## Security Features

1. **Authentication Required:** Only logged-in admins can access the endpoint
2. **Ownership Validation:** Admins can only delete events they created
3. **Session Validation:** Uses Flask session to verify admin identity
4. **Error Handling:** Comprehensive error handling for all edge cases
5. **Graceful Degradation:** Continues even if folders don't exist

## Data Cleanup

When an event is deleted, the following data is removed:

### File System
- `uploads/<event_id>/` - All original uploaded photos
- `uploads/<event_id>/<event_id>_qr.png` - Event QR code
- `uploads/<event_id>/thumbnail_*.jpg` - Event thumbnail
- `processed/<event_id>/` - All processed photos organized by person
- `processed/<event_id>/person_*/individual/` - Individual photos
- `processed/<event_id>/person_*/group/` - Group photos

### Database/JSON
- Event entry removed from `events_data.json`
- Event metadata (name, location, date, category, etc.)
- Photo count
- Creation timestamp
- Admin ownership information

## Important Notes

### Face Recognition Data
⚠️ **Note:** Deleting an event does NOT remove face encodings from `known_faces.dat`. 

The face recognition model maintains learned identities across all events. If you need to remove specific face data, you would need to:
1. Delete or reset `backend/known_faces.dat`
2. Reprocess all remaining events

This is by design to maintain face recognition accuracy across events.

### Irreversible Action
⚠️ **Warning:** Event deletion is permanent and cannot be undone. All photos and data are permanently removed from the file system.

### Concurrent Access
The implementation uses file-based storage (`events_data.json`). In high-concurrency scenarios, consider:
- Adding file locking mechanisms
- Migrating to a proper database with transaction support
- Implementing soft deletes (marking as deleted instead of removing)

## Future Enhancements

Potential improvements for this feature:

1. **Soft Delete:** Mark events as deleted instead of removing them
2. **Trash/Recycle Bin:** Allow recovery within a time window
3. **Bulk Delete:** Delete multiple events at once
4. **Cascade Options:** Choose whether to keep/delete face data
5. **Audit Log:** Track who deleted what and when
6. **Confirmation Email:** Send confirmation to admin after deletion
7. **Archive Feature:** Archive old events instead of deleting
8. **Storage Analytics:** Show storage space that will be freed

## API Documentation Update

Add to your API documentation:

```markdown
### DELETE /api/delete_event/<event_id>

Delete an event and all associated data.

**Authentication:** Admin required

**Parameters:**
- `event_id` (path) - The unique identifier of the event to delete

**Returns:**
- `200 OK` - Event deleted successfully
- `401 Unauthorized` - Not authenticated as admin
- `403 Forbidden` - Not the event owner
- `404 Not Found` - Event doesn't exist
- `500 Internal Server Error` - Deletion failed

**Example:**
```bash
curl -X DELETE http://localhost:5000/api/delete_event/event_abc123 \
  -H "Cookie: session=..."
```
```

## Troubleshooting

### Issue: "Failed to delete event"
**Cause:** File system permissions or disk errors
**Solution:** Check server logs for specific error, verify folder permissions

### Issue: "You can only delete events you created"
**Cause:** Trying to delete another admin's event
**Solution:** Only the admin who created the event can delete it

### Issue: Event deleted but folders remain
**Cause:** File system permissions or path issues
**Solution:** Check server logs, manually remove folders if needed

### Issue: Event deleted but still appears in list
**Cause:** Frontend cache or events_data.json not updated
**Solution:** Refresh the page, check events_data.json file

## Related Files

- `backend/app.py` - Main implementation
- `frontend/pages/event_organizer.html` - UI and JavaScript
- `backend/test_event_deletion.py` - Test suite
- `events_data.json` - Event metadata storage
- `PROJECT_ARCHITECTURE.md` - System architecture documentation

## Version History

- **v1.0** (2024-12-13) - Initial implementation
  - DELETE endpoint added
  - Frontend integration
  - Test suite created
  - Documentation completed
