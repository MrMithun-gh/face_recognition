# Admin Original Photos Fix

## Problem
Admin was seeing duplicate photos because the system was showing processed copies from the `processed` folder. Each photo was duplicated multiple times based on how many people were detected in it.

For example:
- 9 original photos uploaded
- System showed 50+ photos (duplicates for each person detected)

## Solution
Changed admin photo viewing to fetch ONLY original uploaded photos from the `uploads` folder, not the processed copies.

## Changes Made

### Backend (app.py)

#### 1. Updated `/api/admin/events/<event_id>/all-photos`
**Before**: Fetched from `processed` folder, showing duplicates
**After**: Fetches from `uploads` folder, showing only originals

```python
# Now fetches from uploads folder
upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], event_id)
```

#### 2. Added `/api/admin/photos/<event_id>/<filename>`
New route to serve original photos directly from uploads folder

#### 3. Simplified `/api/admin/photos/delete`
**Before**: Required `person_id`, `photo_type`, `filename`
**After**: Only requires `event_id`, `filename`

Deletes only from uploads folder and reminds admin to reprocess.

### Frontend (event_organizer.html)

#### 1. Updated `showPhotosModal()`
- Removed type badges (👤 Individual / 👥 Group)
- Shows clean grid of original photos only
- Changed title to "Original Photos"

#### 2. Updated `deleteCurrentPhoto()`
- Simplified parameters (no person_id or photo_type)
- Added warning about reprocessing requirement
- Uses only filename for deletion

## Result

✅ Admin now sees exactly 9 photos (the originals)
✅ No duplicate photos
✅ No type badges (individual/group)
✅ Clean, simple photo management
✅ Deletion works correctly

## Important Notes

### After Deleting Photos
When an admin deletes a photo from uploads, they need to run the reprocessing script to update face recognition:

```bash
cd backend
python reprocess_photos.py
```

This will:
1. Clear processed folder
2. Clear face recognition model
3. Reprocess remaining photos
4. Update face detection

### Photo Flow
1. **Upload**: Photos go to `uploads/event_id/`
2. **Processing**: System creates copies in `processed/event_id/person_id/`
3. **Admin View**: Shows only originals from `uploads/`
4. **User View**: Shows processed copies from `processed/`

## Testing

- [x] Admin sees only 9 original photos
- [x] No duplicate photos displayed
- [x] No type badges shown
- [x] Photos load correctly
- [x] Fullscreen viewer works
- [x] Delete functionality works
- [x] Photo count updates after deletion
- [x] Reprocessing script works after deletion

## Files Modified

1. `backend/app.py`
   - Modified `/api/admin/events/<event_id>/all-photos`
   - Added `/api/admin/photos/<event_id>/<filename>`
   - Simplified `/api/admin/photos/delete`

2. `frontend/pages/event_organizer.html`
   - Updated `showPhotosModal()` function
   - Updated `deleteCurrentPhoto()` function
   - Removed type badge display logic

3. `ADMIN_PHOTO_ACCESS_FEATURE.md`
   - Updated documentation to reflect changes

4. `ADMIN_ORIGINAL_PHOTOS_FIX.md`
   - Created this documentation
