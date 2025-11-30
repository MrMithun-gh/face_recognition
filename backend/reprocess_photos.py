#!/usr/bin/env python3
"""
Script to reprocess all photos in the uploads folder.
This will clear the processed folder and face model, then reprocess everything.
"""

import os
import sys
import shutil

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import process_images, UPLOAD_FOLDER, PROCESSED_FOLDER, KNOWN_FACES_DATA_PATH

def reprocess_all_events():
    """Reprocess all events by clearing processed data and running processing again."""
    
    print("=" * 60)
    print("PHOTO REPROCESSING SCRIPT")
    print("=" * 60)
    
    # Step 1: Clear the processed folder
    print("\n[1/4] Clearing processed folder...")
    if os.path.exists(PROCESSED_FOLDER):
        try:
            shutil.rmtree(PROCESSED_FOLDER)
            print(f"✓ Removed: {PROCESSED_FOLDER}")
        except Exception as e:
            print(f"✗ Error removing processed folder: {e}")
            return
    
    os.makedirs(PROCESSED_FOLDER, exist_ok=True)
    print(f"✓ Created fresh: {PROCESSED_FOLDER}")
    
    # Step 2: Clear the face model
    print("\n[2/4] Clearing face recognition model...")
    if os.path.exists(KNOWN_FACES_DATA_PATH):
        try:
            os.remove(KNOWN_FACES_DATA_PATH)
            print(f"✓ Removed: {KNOWN_FACES_DATA_PATH}")
        except Exception as e:
            print(f"✗ Error removing face model: {e}")
    
    # Step 3: Find all events
    print("\n[3/4] Finding events to process...")
    if not os.path.exists(UPLOAD_FOLDER):
        print(f"✗ Upload folder not found: {UPLOAD_FOLDER}")
        return
    
    events = [d for d in os.listdir(UPLOAD_FOLDER) 
              if os.path.isdir(os.path.join(UPLOAD_FOLDER, d))]
    
    if not events:
        print("✗ No events found to process")
        return
    
    print(f"✓ Found {len(events)} event(s): {', '.join(events)}")
    
    # Step 4: Process each event
    print("\n[4/4] Processing events...")
    for i, event_id in enumerate(events, 1):
        print(f"\n--- Processing event {i}/{len(events)}: {event_id} ---")
        
        event_dir = os.path.join(UPLOAD_FOLDER, event_id)
        photo_files = [f for f in os.listdir(event_dir) 
                      if f.lower().endswith(('.png', '.jpg', '.jpeg')) 
                      and not f.endswith('_qr.png')]
        
        print(f"    Photos to process: {len(photo_files)}")
        
        try:
            process_images(event_id)
            print(f"✓ Successfully processed: {event_id}")
        except Exception as e:
            print(f"✗ Error processing {event_id}: {e}")
    
    print("\n" + "=" * 60)
    print("REPROCESSING COMPLETE!")
    print("=" * 60)
    print("\nYou can now:")
    print("1. Restart your Flask server")
    print("2. Scan your face to find photos")
    print("=" * 60)

if __name__ == '__main__':
    try:
        reprocess_all_events()
    except KeyboardInterrupt:
        print("\n\n✗ Reprocessing cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Fatal error: {e}")
        sys.exit(1)
