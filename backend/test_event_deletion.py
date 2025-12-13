"""
Test suite for event deletion functionality
"""
import pytest
import json
import os
import tempfile
import shutil
from app import app, EVENTS_DATA_PATH


@pytest.fixture
def client():
    """Create a test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def admin_session(client):
    """Create an admin session"""
    with client.session_transaction() as sess:
        sess['admin_logged_in'] = True
        sess['admin_id'] = 1
        sess['admin_email'] = 'test@admin.com'
        sess['admin_organization'] = 'Test Org'
    return client


@pytest.fixture
def mock_event_data(tmp_path):
    """Create mock event data"""
    # Create temporary directories
    upload_dir = tmp_path / "uploads" / "event_test123"
    processed_dir = tmp_path / "processed" / "event_test123"
    upload_dir.mkdir(parents=True)
    processed_dir.mkdir(parents=True)
    
    # Create some test files
    (upload_dir / "test_photo.jpg").write_text("fake image data")
    (processed_dir / "person_0001").mkdir()
    (processed_dir / "person_0001" / "individual").mkdir()
    (processed_dir / "person_0001" / "individual" / "photo1.jpg").write_text("fake image")
    
    # Create mock events data
    events_data = [
        {
            "id": "event_test123",
            "name": "Test Event",
            "location": "Test Location",
            "date": "2024-12-15",
            "category": "Festival",
            "image": "/static/images/default_event.jpg",
            "photos_count": 1,
            "qr_code": "/api/qr_code/event_test123",
            "created_by_admin_id": 1,
            "created_by_user_id": None,
            "created_at": "2024-12-01T10:00:00"
        },
        {
            "id": "event_other456",
            "name": "Other Event",
            "location": "Other Location",
            "date": "2024-12-20",
            "category": "Corporate",
            "image": "/static/images/default_event.jpg",
            "photos_count": 0,
            "qr_code": "/api/qr_code/event_other456",
            "created_by_admin_id": 2,
            "created_by_user_id": None,
            "created_at": "2024-12-02T10:00:00"
        }
    ]
    
    return {
        'events_data': events_data,
        'upload_dir': upload_dir,
        'processed_dir': processed_dir,
        'tmp_path': tmp_path
    }


class TestEventDeletion:
    """Test cases for event deletion"""
    
    def test_delete_event_unauthorized(self, client):
        """Test that unauthenticated users cannot delete events"""
        response = client.delete('/api/delete_event/event_test123')
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Unauthorized' in data['error']
    
    def test_delete_event_not_found(self, admin_session, monkeypatch):
        """Test deleting a non-existent event"""
        # Mock empty events data
        def mock_exists(path):
            return True
        
        def mock_open(path, mode='r'):
            if 'events_data.json' in path:
                return tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json')
        
        monkeypatch.setattr(os.path, 'exists', mock_exists)
        
        # Create temporary events file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump([], f)
            temp_file = f.name
        
        monkeypatch.setattr('app.EVENTS_DATA_PATH', temp_file)
        
        response = admin_session.delete('/api/delete_event/nonexistent_event')
        
        # Cleanup
        os.unlink(temp_file)
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'not found' in data['error'].lower()
    
    def test_delete_event_wrong_owner(self, admin_session, mock_event_data, monkeypatch):
        """Test that admin cannot delete another admin's event"""
        # Create temporary events file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(mock_event_data['events_data'], f)
            temp_file = f.name
        
        monkeypatch.setattr('app.EVENTS_DATA_PATH', temp_file)
        
        # Try to delete event owned by admin_id=2 while logged in as admin_id=1
        response = admin_session.delete('/api/delete_event/event_other456')
        
        # Cleanup
        os.unlink(temp_file)
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'only delete events you created' in data['error'].lower()
    
    def test_delete_event_success(self, admin_session, mock_event_data, monkeypatch):
        """Test successful event deletion"""
        # Create temporary events file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(mock_event_data['events_data'], f)
            temp_file = f.name
        
        # Mock the paths
        monkeypatch.setattr('app.EVENTS_DATA_PATH', temp_file)
        monkeypatch.setattr('app.UPLOAD_FOLDER', str(mock_event_data['tmp_path'] / 'uploads'))
        monkeypatch.setattr('app.PROCESSED_FOLDER', str(mock_event_data['tmp_path'] / 'processed'))
        
        # Verify folders exist before deletion
        assert mock_event_data['upload_dir'].exists()
        assert mock_event_data['processed_dir'].exists()
        
        # Delete the event
        response = admin_session.delete('/api/delete_event/event_test123')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'deleted successfully' in data['message'].lower()
        
        # Verify folders are deleted
        assert not mock_event_data['upload_dir'].exists()
        assert not mock_event_data['processed_dir'].exists()
        
        # Verify event removed from events_data.json
        with open(temp_file, 'r') as f:
            remaining_events = json.load(f)
        
        assert len(remaining_events) == 1
        assert remaining_events[0]['id'] == 'event_other456'
        
        # Cleanup
        os.unlink(temp_file)
    
    def test_delete_event_missing_folders(self, admin_session, mock_event_data, monkeypatch):
        """Test deletion when folders don't exist (should still succeed)"""
        # Create temporary events file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(mock_event_data['events_data'], f)
            temp_file = f.name
        
        # Mock the paths to non-existent directories
        monkeypatch.setattr('app.EVENTS_DATA_PATH', temp_file)
        monkeypatch.setattr('app.UPLOAD_FOLDER', str(mock_event_data['tmp_path'] / 'nonexistent_uploads'))
        monkeypatch.setattr('app.PROCESSED_FOLDER', str(mock_event_data['tmp_path'] / 'nonexistent_processed'))
        
        # Delete the event
        response = admin_session.delete('/api/delete_event/event_test123')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        
        # Verify event removed from events_data.json
        with open(temp_file, 'r') as f:
            remaining_events = json.load(f)
        
        assert len(remaining_events) == 1
        assert remaining_events[0]['id'] == 'event_other456'
        
        # Cleanup
        os.unlink(temp_file)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
