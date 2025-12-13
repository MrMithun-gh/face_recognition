# PicMe - Project Architecture & Implementation

## 📋 Project Overview
**PicMe** is a facial recognition-based event photo management system that allows users to find and download their photos from events using biometric authentication.

---

## 🏗️ System Architecture

```mermaid
graph TB
    subgraph "Frontend Layer"
        A[HTML Pages] --> B[JavaScript]
        B --> C[CSS Styling]
        A --> D[QR Scanner]
    end
    
    subgraph "Backend Layer - Flask API"
        E[app.py - Main Server] --> F[Face Recognition API]
        E --> G[Event Management API]
        E --> H[User Authentication API]
        E --> I[Admin Management API]
        E --> J[Photo Download API]
    end
    
    subgraph "ML/AI Layer"
        K[face_model.py] --> L[Face Recognition Model]
        M[face_utils.py] --> N[Liveness Detection]
        M --> O[Face Alignment]
        M --> P[Quality Assessment]
    end
    
    subgraph "Data Storage"
        Q[(PostgreSQL/Neon DB)]
        R[File System - Uploads]
        S[File System - Processed]
        T[events_data.json]
        U[known_faces.dat]
    end
    
    A --> E
    F --> K
    F --> M
    E --> Q
    E --> R
    E --> S
    E --> T
    K --> U
    
    style A fill:#e1f5ff
    style E fill:#fff4e1
    style K fill:#ffe1f5
    style Q fill:#e1ffe1
```

---

## 📚 Technology Stack & Libraries

### Backend Dependencies (Python)
```
┌─────────────────────────────────────────────────────────┐
│ Core Framework                                          │
├─────────────────────────────────────────────────────────┤
│ • Flask 2.0.1          - Web framework                  │
│ • Werkzeug 2.0.1       - WSGI utilities & password hash │
│ • python-dotenv 0.19.0 - Environment variable management│
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Machine Learning & Computer Vision                      │
├─────────────────────────────────────────────────────────┤
│ • face-recognition 1.3.0 - Face detection & recognition │
│ • dlib (implicit)        - Facial landmarks (68 points) │
│ • numpy 1.21.2           - Numerical computations       │
│ • opencv-python 4.5.3.56 - Image processing & CV       │
│ • Pillow 8.3.1           - Image manipulation           │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Database & Storage                                      │
├─────────────────────────────────────────────────────────┤
│ • psycopg2-binary 2.9.9      - PostgreSQL adapter       │
│ • mysql-connector-python 8.0.27 - MySQL support (legacy)│
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Utilities                                               │
├─────────────────────────────────────────────────────────┤
│ • qrcode 7.4.2  - QR code generation for events         │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Testing                                                 │
├─────────────────────────────────────────────────────────┤
│ • pytest 7.4.3      - Unit testing framework            │
│ • hypothesis 6.92.1 - Property-based testing            │
└─────────────────────────────────────────────────────────┘
```

### Frontend Technologies
```
┌─────────────────────────────────────────────────────────┐
│ Core Technologies                                       │
├─────────────────────────────────────────────────────────┤
│ • HTML5          - Page structure                       │
│ • CSS3           - Styling (main.css)                   │
│ • JavaScript ES6 - Client-side logic                    │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Browser APIs                                            │
├─────────────────────────────────────────────────────────┤
│ • MediaDevices API - Webcam access                      │
│ • Canvas API       - Image processing                   │
│ • Fetch API        - HTTP requests                      │
│ • LocalStorage     - Client-side storage                │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ External Libraries                                      │
├─────────────────────────────────────────────────────────┤
│ • qr-scanner.js - QR code scanning functionality        │
└─────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow Architecture

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant API as Flask API
    participant ML as Face Model
    participant DB as Database
    participant FS as File System

    Note over U,FS: Event Creation Flow
    U->>F: Create Event
    F->>API: POST /api/create_event
    API->>FS: Create event folders
    API->>FS: Generate QR code
    API->>DB: Save event metadata
    API-->>F: Event created

    Note over U,FS: Photo Upload & Processing Flow
    U->>F: Upload Photos
    F->>API: POST /api/upload_photos
    API->>FS: Save to uploads/event_id/
    API->>ML: Process images (background)
    ML->>ML: Detect faces
    ML->>ML: Learn/Match identities
    ML->>FS: Organize by person_id
    ML->>FS: Save to processed/event_id/person_id/

    Note over U,FS: Face Recognition Flow
    U->>F: Scan Face (webcam)
    F->>API: POST /recognize (multi-frame)
    API->>ML: Verify liveness
    ML-->>API: Liveness result
    API->>ML: Aggregate encoding
    ML->>ML: Match against known faces
    ML-->>API: person_id
    API->>FS: Locate photos
    API-->>F: Return photo URLs
    F-->>U: Display photos

    Note over U,FS: Download Flow
    U->>F: Select photos
    F->>API: POST /api/download_photos
    API->>FS: Create ZIP file
    API-->>F: Send ZIP
    F-->>U: Download ZIP
    API->>API: Cleanup ZIP (background)
```

---

## 📁 Project Structure

```
picme/
│
├── backend/
│   ├── app.py                          # Main Flask application (951 lines)
│   ├── face_model.py                   # ML model for face recognition
│   ├── face_utils.py                   # Face processing utilities
│   ├── requirements.txt                # Python dependencies
│   ├── .env                            # Environment variables
│   ├── known_faces.dat                 # Serialized face encodings
│   ├── shape_predictor_68_face_landmarks.dat  # Dlib model
│   ├── test_*.py                       # Test files
│   └── reprocess_photos.py             # Batch reprocessing utility
│
├── frontend/
│   ├── pages/
│   │   ├── index.html                  # Landing page
│   │   ├── homepage.html               # User dashboard
│   │   ├── login.html                  # User login
│   │   ├── signup.html                 # User registration
│   │   ├── event_discovery.html        # Browse events
│   │   ├── event_detail.html           # Event photo gallery
│   │   ├── biometric_authentication_portal.html  # Face scan
│   │   ├── personal_photo_gallery.html # User's photos
│   │   ├── download_page.html          # Download interface
│   │   └── event_organizer.html        # Admin dashboard
│   ├── main.css                        # Global styles
│   ├── gallery.js                      # Gallery functionality
│   ├── qr-scanner.js                   # QR scanning library
│   └── picme.svg                       # Logo
│
├── uploads/                            # Original uploaded photos
│   └── event_{id}/
│       ├── {photo_files}
│       └── {event_id}_qr.png
│
├── processed/                          # Processed & organized photos
│   └── event_{id}/
│       └── person_{id}/
│           ├── individual/             # Solo photos
│           └── group/                  # Group photos (watermarked_)
│
├── .kiro/
│   └── specs/                          # Feature specifications
│       ├── admin-event-editing/
│       └── download-page/
│
├── events_data.json                    # Event metadata cache
└── *.md                                # Documentation files
```

---

## 🔐 Authentication & Authorization

```mermaid
graph LR
    A[User Types] --> B[Regular User]
    A --> C[Event Organizer]
    A --> D[Admin]
    
    B --> E[Login via Email/Password]
    B --> F[Biometric Face Scan]
    
    C --> G[Create Events]
    C --> H[Upload Photos]
    
    D --> I[Admin Dashboard]
    D --> J[Event Management]
    D --> K[Access Original Photos]
    
    E --> L[Session Management]
    F --> M[person_id in Session]
    
    style B fill:#e1f5ff
    style C fill:#fff4e1
    style D fill:#ffe1e1
```

### Session Variables
```python
# Regular User Session
{
    'logged_in': True,
    'user_id': int,
    'user_email': str,
    'user_type': 'user' | 'organizer',
    'person_id': str  # Set after face recognition
}

# Admin Session
{
    'admin_logged_in': True,
    'admin_id': int,
    'admin_email': str,
    'admin_organization': str
}
```

---

## 🧠 Machine Learning Pipeline

```mermaid
graph TB
    subgraph "Face Recognition Model"
        A[Input: Photo] --> B[Face Detection]
        B --> C[Face Encoding - 128D Vector]
        C --> D{Match Existing?}
        D -->|Yes| E[Update Person Encoding]
        D -->|No| F[Create New Person ID]
        E --> G[Save Model]
        F --> G
    end
    
    subgraph "Liveness Detection"
        H[Multi-frame Input] --> I[Motion Analysis]
        H --> J[Blink Detection - EAR]
        H --> K[Head Turn Detection]
        I --> L{Liveness Check}
        J --> L
        K --> L
        L -->|Pass| M[Proceed to Recognition]
        L -->|Fail| N[Reject - Spoof Detected]
    end
    
    subgraph "Quality Assessment"
        O[Frame] --> P[Sharpness - Laplacian]
        O --> Q[Brightness Analysis]
        P --> R[Quality Score 0-1]
        Q --> R
        R --> S[Weighted Aggregation]
    end
    
    style A fill:#e1f5ff
    style H fill:#ffe1f5
    style O fill:#fff4e1
```

### Face Model Features
- **Multi-sample Learning**: Stores up to 15 encodings per person
- **Dynamic Tolerance**: 0.55 (strict) to 0.60 (relaxed)
- **Continuous Improvement**: Updates encodings with high-quality scans
- **Persistence**: Serialized to `known_faces.dat` using pickle

### Liveness Detection Features
- **Eye Aspect Ratio (EAR)**: Detects blinks (OPEN > 0.24, CLOSED < 0.19)
- **Motion Detection**: Requires minimum 3.5 pixel difference between frames
- **Head Turn**: Tracks horizontal face center movement (min 22% of face width)
- **Challenge Types**: BLINK, HEAD_TURN, or AUTO (either)

---

## 🌐 API Endpoints

### Public Routes
```
GET  /                          - Landing page
GET  /login                     - Login page
GET  /signup                    - Signup page
GET  /events                    - Get all events (JSON)
```

### User Routes (Authentication Required)
```
POST /register                  - User registration
POST /login                     - User login
GET  /logout                    - User logout
GET  /homepage                  - User dashboard
GET  /event_discovery           - Browse events
GET  /event_detail              - Event details
GET  /biometric_authentication_portal - Face scan page
GET  /personal_photo_gallery    - User's photos
GET  /download_page             - Download interface
POST /recognize                 - Face recognition
GET  /api/user_photos           - Get user's photos
POST /api/download_photos       - Download photos as ZIP
POST /api/download_event_photos - Download event photos
```

### Admin Routes (Admin Authentication Required)
```
POST   /admin/register            - Admin registration
POST   /admin/login               - Admin login
GET    /admin/logout              - Admin logout
GET    /event_organizer           - Admin dashboard
POST   /api/create_event          - Create new event
POST   /api/upload_photos/:id     - Upload event photos
GET    /api/my_events             - Get admin's events
PUT    /api/events/:id            - Update event details
POST   /api/events/:id/thumbnail  - Update event thumbnail
DELETE /api/delete_event/:id      - Delete event and all data
GET    /api/admin/events/:id/all-photos - Get original photos
```

### Photo Serving Routes
```
GET  /photos/:event/:person/:type/:file  - Private photos
GET  /photos/:event/all/:file            - Public photos
GET  /api/events/:id/photos              - Event photo list
GET  /api/events/:id/thumbnail           - Event thumbnail
GET  /api/qr_code/:id                    - Event QR code
```

---

## 💾 Database Schema

```sql
-- Users Table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    user_type VARCHAR(50) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Admins Table
CREATE TABLE admins (
    id SERIAL PRIMARY KEY,
    organization_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### File-based Storage
```json
// events_data.json
{
  "id": "event_abc123",
  "name": "Summer Festival 2024",
  "location": "Central Park",
  "date": "2024-07-15",
  "category": "Festival",
  "image": "/api/events/event_abc123/thumbnail",
  "thumbnail_filename": "thumbnail_xyz789.jpg",
  "photos_count": 150,
  "qr_code": "/api/qr_code/event_abc123",
  "created_by_admin_id": 1,
  "created_by_user_id": null,
  "created_at": "2024-07-01T10:00:00",
  "sample_photos": []
}
```

---

## 🔧 Key Features Implementation

### 1. Face Recognition
- **Algorithm**: face_recognition library (dlib-based)
- **Encoding**: 128-dimensional face vectors
- **Matching**: Euclidean distance with dynamic thresholds
- **Learning**: Incremental learning with quality-weighted aggregation

### 2. Liveness Detection
- **Anti-spoofing**: Prevents photo/screen attacks
- **Multi-modal**: Combines motion, blink, and head turn
- **Real-time**: Processes webcam frames in browser

### 3. Photo Organization
- **Automatic**: Classifies as individual (1 face) or group (2+ faces)
- **Privacy**: Person-specific folders with unique IDs
- **Watermarking**: Group photos prefixed with "watermarked_"

### 4. Event Management
- **QR Codes**: Auto-generated for easy event access
- **Thumbnails**: Custom event images
- **Categories**: Organized by event type
- **Ownership**: Admin/user isolation

### 5. Download System
- **Bulk Download**: ZIP file generation
- **Size Limits**: 100MB max, 500 photos max
- **Cleanup**: Automatic temporary file removal
- **Error Handling**: Comprehensive validation

---

## 🧪 Testing Strategy

### Unit Tests
```python
# test_event_creation.py
- Event creation validation
- Photo upload handling
- Event metadata management

# test_user_photos_api.py
- User photo retrieval
- Session validation
- Error handling

# test_error_handling.py
- Edge cases
- Error responses
- Input validation
```

### Property-Based Tests
```python
# Using Hypothesis library
- Face encoding consistency
- Liveness detection reliability
- Photo organization correctness
```

---

## 🚀 Deployment Configuration

### Environment Variables
```bash
DATABASE_URL=postgresql://user:pass@host/db?sslmode=require
FLASK_SECRET_KEY=your_secret_key_here
```

### Production Considerations
- **Database**: Neon PostgreSQL (serverless)
- **File Storage**: Local filesystem (can migrate to S3/Cloud Storage)
- **Caching**: Disabled for development (Cache-Control headers)
- **Sessions**: Server-side with Flask sessions
- **HTTPS**: Required for webcam access

---

## 📊 Performance Characteristics

### Face Recognition
- **Detection Time**: ~100-300ms per image
- **Encoding Time**: ~50-150ms per face
- **Matching Time**: ~1-5ms per comparison
- **Model Size**: ~1-10MB (depends on # of people)

### Photo Processing
- **Background Processing**: Threaded, non-blocking
- **Batch Processing**: Handles multiple photos per event
- **Storage**: Organized by event → person → type

### Download Performance
- **ZIP Creation**: ~1-5 seconds for 50 photos
- **Streaming**: Direct file send with cleanup
- **Limits**: 100MB max ZIP size

---

## 🔒 Security Features

1. **Password Hashing**: Werkzeug PBKDF2 SHA-256
2. **Session Management**: Secure Flask sessions
3. **Input Validation**: Comprehensive parameter checking
4. **Path Sanitization**: Prevents directory traversal
5. **File Type Validation**: Whitelist for images
6. **Authentication Guards**: Decorators for protected routes
7. **Admin Isolation**: Separate admin/user sessions
8. **Liveness Detection**: Anti-spoofing for face recognition

---

## 📈 Future Enhancements

- [ ] Cloud storage integration (AWS S3, Google Cloud Storage)
- [ ] Real-time photo processing notifications
- [ ] Advanced face clustering algorithms
- [ ] Mobile app development
- [ ] Social sharing features
- [ ] Payment integration for premium features
- [ ] Analytics dashboard for event organizers
- [ ] Multi-language support

---

*Generated: December 2024*
*Version: 1.0*
