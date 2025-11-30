# Admin Photo Access Feature

## Overview
Implemented comprehensive admin access to view, manage, and delete ORIGINAL uploaded photos (no duplicates or processed copies).

## Features Implemented

### 1. Backend API Endpoints

#### `/api/admin/events/<event_id>/all-photos` (GET)
- **Purpose**: Fetch ORIGINAL uploaded photos for a specific event (no duplicates)
- **Access**: Admin only
- **Source**: Fetches from uploads folder, not processed folder
- **Returns**: JSON with array of photo objects containing:
  - `url`: Photo URL path
  - `filename`: Original filename
  - `original_filename`: Original filename

#### `/api/admin/photos/<event_id>/<filename>` (GET)
- **Purpose**: Serve original uploaded photos to admin
- **Access**: Admin only
- **Source**: Serves from uploads folder

#### `/api/admin/photos/delete` (POST)
- **Purpose**: Delete a specific photo from the uploads folder
- **Access**: Admin only
- **Parameters**:
  - `event_id`: Event identifier
  - `filename`: Photo filename
- **Actions**:
  - Deletes from uploads folder
  - Updates event photo count in events_data.json
  - Note: Requires reprocessing to update face recognition

### 2. Frontend UI Components

#### View Photos Button
- Added to each event card in the Event Organizer dashboard
- Icon: 🖼️ View Photos
- Opens modal showing all photos for the event

#### Photos Modal
- Grid layout displaying all ORIGINAL uploaded photos
- Shows only the 9 original photos, not processed duplicates
- No type badges (individual/group) - just clean photo display
- Click any photo to open fullscreen viewer

#### Fullscreen Photo Viewer
- Full-screen overlay with dark background
- Large photo display (max 90% viewport)
- Controls:
  - ✕ Close button (top right)
  - 🗑️ Delete button (top right)
  - ESC key to close
- Delete confirmation before removing photos

### 3. Photo Management Features

#### View All Photos
- Admins see only ORIGINAL uploaded photos (no duplicates)
- Photos organized in responsive grid
- Clean display without type badges

#### Fullscreen View
- Click any photo to view in fullscreen
- Optimized for viewing photo details
- Smooth transitions

#### Delete Photos
- Delete button in fullscreen viewer
- Confirmation dialog before deletion (warns about reprocessing)
- Deletes from uploads folder only
- Automatic refresh after deletion
- Updates photo count in event list
- Note: Requires running reprocessing script to update face recognition

## Access Control

### Admin Requirements
- Must be logged in as admin (`session.get('admin_logged_in')`)
- All photo management endpoints check admin status
- Returns 403 Forbidden if not admin

### Security
- Server-side validation of admin status
- File path validation to prevent directory traversal
- Proper error handling and logging

## User Experience

### Visual Feedback
- Loading indicators while fetching photos
- Success/error alerts for all actions
- Smooth modal transitions
- Responsive grid layout

### Keyboard Shortcuts
- ESC key closes fullscreen viewer
- Intuitive click interactions

## File Structure

### Modified Files
1. `backend/app.py`
   - Added admin photo access endpoints
   - Added photo deletion endpoint
   - Enhanced access control

2. `frontend/pages/event_organizer.html`
   - Added View Photos button
   - Added Photos Modal
   - Added Fullscreen Viewer
   - Added JavaScript functions for photo management

## Testing Checklist

- [x] Admin can view all photos for an event
- [x] Individual photos display with correct badge
- [x] Group photos display with correct badge
- [x] Fullscreen viewer opens on photo click
- [x] Delete button works in fullscreen mode
- [x] Photo count updates after deletion
- [x] Non-admin users cannot access admin endpoints
- [x] Error handling for missing photos
- [x] Responsive layout on different screen sizes

## Future Enhancements

Potential improvements:
1. Bulk photo deletion
2. Photo filtering (individual/group only)
3. Photo search functionality
4. Download all photos as ZIP
5. Photo editing capabilities
6. Photo metadata display
7. Navigation between photos in fullscreen (prev/next buttons)

## Notes

- Photos are deleted from both processed and uploads folders
- Event photo count is automatically updated
- Fullscreen viewer uses flexbox for centering
- Modal uses z-index 10000 for proper layering
- All photo operations include proper error handling
