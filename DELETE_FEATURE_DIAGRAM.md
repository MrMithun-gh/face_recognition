# Admin Event Deletion - Visual Architecture

## 🏗️ Complete System Flow

```mermaid
graph TB
    subgraph "Frontend - Event Organizer Page"
        A[Event Card] --> B[Delete Button]
        B --> C[Confirmation Modal]
        C --> D{User Confirms?}
        D -->|Yes| E[Send DELETE Request]
        D -->|No| F[Close Modal]
    end
    
    subgraph "Backend - Flask API"
        E --> G[DELETE /api/delete_event/event_id]
        G --> H{Admin Authenticated?}
        H -->|No| I[Return 401 Unauthorized]
        H -->|Yes| J{Event Exists?}
        J -->|No| K[Return 404 Not Found]
        J -->|Yes| L{Admin Owns Event?}
        L -->|No| M[Return 403 Forbidden]
        L -->|Yes| N[Delete Event Data]
    end
    
    subgraph "File System Operations"
        N --> O[Delete uploads/event_id/]
        N --> P[Delete processed/event_id/]
        N --> Q[Update events_data.json]
    end
    
    subgraph "Response & UI Update"
        O --> R[Return 200 Success]
        P --> R
        Q --> R
        R --> S[Show Success Alert]
        S --> T[Refresh Event List]
        T --> U[Event Card Disappears]
    end
    
    I --> V[Show Error Alert]
    K --> V
    M --> V
    
    style B fill:#ff6b6b
    style C fill:#ffd93d
    style N fill:#6bcf7f
    style R fill:#4ecdc4
```

## 🔄 Data Flow Diagram

```mermaid
sequenceDiagram
    participant Admin
    participant Browser
    participant Flask
    participant FileSystem
    participant JSON

    Admin->>Browser: Click Delete Button
    Browser->>Admin: Show Confirmation Modal
    Admin->>Browser: Confirm Deletion
    
    Browser->>Flask: DELETE /api/delete_event/event_123
    
    Flask->>Flask: Check Admin Session
    alt Not Authenticated
        Flask->>Browser: 401 Unauthorized
        Browser->>Admin: Show Error
    else Authenticated
        Flask->>JSON: Load events_data.json
        Flask->>Flask: Find Event
        
        alt Event Not Found
            Flask->>Browser: 404 Not Found
            Browser->>Admin: Show Error
        else Event Found
            Flask->>Flask: Check Ownership
            
            alt Wrong Owner
                Flask->>Browser: 403 Forbidden
                Browser->>Admin: Show Error
            else Correct Owner
                Flask->>FileSystem: Delete uploads/event_123/
                FileSystem-->>Flask: Deleted
                
                Flask->>FileSystem: Delete processed/event_123/
                FileSystem-->>Flask: Deleted
                
                Flask->>JSON: Remove Event Entry
                Flask->>JSON: Save events_data.json
                JSON-->>Flask: Saved
                
                Flask->>Browser: 200 Success
                Browser->>Admin: Show Success Message
                Browser->>Browser: Refresh Event List
                Browser->>Admin: Event Removed from UI
            end
        end
    end
```

## 📁 File Structure Changes

### Before Deletion
```
project/
├── uploads/
│   ├── event_abc123/           ← TO BE DELETED
│   │   ├── photo1.jpg
│   │   ├── photo2.jpg
│   │   ├── thumbnail_xyz.jpg
│   │   └── event_abc123_qr.png
│   └── event_def456/           ← KEPT (different event)
│       └── ...
├── processed/
│   ├── event_abc123/           ← TO BE DELETED
│   │   ├── person_0001/
│   │   │   ├── individual/
│   │   │   └── group/
│   │   └── person_0002/
│   │       ├── individual/
│   │       └── group/
│   └── event_def456/           ← KEPT (different event)
│       └── ...
└── events_data.json
    [
      {
        "id": "event_abc123",   ← TO BE REMOVED
        "name": "Summer Fest",
        ...
      },
      {
        "id": "event_def456",   ← KEPT
        "name": "Tech Conf",
        ...
      }
    ]
```

### After Deletion
```
project/
├── uploads/
│   └── event_def456/           ✅ KEPT
│       └── ...
├── processed/
│   └── event_def456/           ✅ KEPT
│       └── ...
└── events_data.json
    [
      {
        "id": "event_def456",   ✅ KEPT
        "name": "Tech Conf",
        ...
      }
    ]
```

## 🔐 Security Flow

```mermaid
graph LR
    A[Request] --> B{Session Valid?}
    B -->|No| C[401 Unauthorized]
    B -->|Yes| D{Admin Role?}
    D -->|No| E[401 Unauthorized]
    D -->|Yes| F{Event Exists?}
    F -->|No| G[404 Not Found]
    F -->|Yes| H{Owns Event?}
    H -->|No| I[403 Forbidden]
    H -->|Yes| J[Delete Event]
    J --> K[200 Success]
    
    style C fill:#ff6b6b
    style E fill:#ff6b6b
    style G fill:#ffa500
    style I fill:#ff6b6b
    style K fill:#6bcf7f
```

## 🎨 UI State Machine

```mermaid
stateDiagram-v2
    [*] --> EventCard: Page Load
    EventCard --> HoverDelete: Mouse Hover
    HoverDelete --> EventCard: Mouse Leave
    HoverDelete --> ModalOpen: Click Delete
    ModalOpen --> ModalOpen: User Reads
    ModalOpen --> EventCard: Click Cancel/Close
    ModalOpen --> Deleting: Click Confirm
    Deleting --> Success: API Success
    Deleting --> Error: API Error
    Success --> EventRemoved: Auto Refresh
    Error --> ModalOpen: Show Error
    EventRemoved --> [*]: Event Gone
```

## 📊 Component Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend Layer                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Event Card   │  │ Delete Button│  │ Confirmation │ │
│  │ Component    │──│ Component    │──│ Modal        │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│         │                  │                  │         │
│         └──────────────────┴──────────────────┘         │
│                            │                            │
│                   ┌────────▼────────┐                   │
│                   │ JavaScript      │                   │
│                   │ Event Handlers  │                   │
│                   └────────┬────────┘                   │
└────────────────────────────┼─────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │  Fetch API      │
                    │  DELETE Request │
                    └────────┬────────┘
                             │
┌────────────────────────────▼─────────────────────────────┐
│                    Backend Layer                         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Flask Route  │  │ Auth Guard   │  │ Ownership    │ │
│  │ Handler      │──│ Middleware   │──│ Validator    │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│         │                                               │
│         └───────────────┬─────────────────────────────┐│
│                         │                             ││
│              ┌──────────▼──────────┐  ┌──────────────▼┤
│              │ File System Manager │  │ JSON Manager  ││
│              │ - Delete uploads/   │  │ - Update data ││
│              │ - Delete processed/ │  │ - Save file   ││
│              └─────────────────────┘  └───────────────┘│
└─────────────────────────────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────┐
│                    Storage Layer                         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ uploads/     │  │ processed/   │  │ events_data  │ │
│  │ [deleted]    │  │ [deleted]    │  │ .json        │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## 🧪 Test Coverage Map

```
Test Suite: test_event_deletion.py
├── ✅ test_delete_event_unauthorized
│   └── Verifies: 401 when not logged in
│
├── ✅ test_delete_event_not_found
│   └── Verifies: 404 when event doesn't exist
│
├── ✅ test_delete_event_wrong_owner
│   └── Verifies: 403 when admin doesn't own event
│
├── ✅ test_delete_event_success
│   ├── Verifies: 200 on successful deletion
│   ├── Verifies: Folders deleted
│   ├── Verifies: JSON updated
│   └── Verifies: Event removed from list
│
└── ✅ test_delete_event_missing_folders
    ├── Verifies: Handles missing folders gracefully
    └── Verifies: Still updates JSON correctly
```

## 📈 Performance Metrics

```
┌─────────────────────────────────────────────────────────┐
│                  Operation Timeline                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  User Click                                              │
│  │                                                       │
│  ├─ 0ms: Modal Opens                                    │
│  │                                                       │
│  ├─ User Confirms                                       │
│  │                                                       │
│  ├─ 10ms: DELETE Request Sent                           │
│  │                                                       │
│  ├─ 50ms: Auth Check                                    │
│  │                                                       │
│  ├─ 100ms: Load JSON                                    │
│  │                                                       │
│  ├─ 150ms: Validate Ownership                           │
│  │                                                       │
│  ├─ 200ms: Delete uploads/ (100-500ms depending on size)│
│  │                                                       │
│  ├─ 400ms: Delete processed/ (100-500ms)                │
│  │                                                       │
│  ├─ 500ms: Update JSON                                  │
│  │                                                       │
│  ├─ 550ms: Response Sent                                │
│  │                                                       │
│  ├─ 600ms: Success Alert Shown                          │
│  │                                                       │
│  └─ 650ms: Event List Refreshed                         │
│                                                          │
│  Total Time: ~650ms (typical)                           │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## 🎯 Error Handling Flow

```mermaid
graph TD
    A[Delete Request] --> B{Try Block}
    B --> C{Auth Check}
    C -->|Fail| D[401 Error]
    C -->|Pass| E{Load JSON}
    E -->|Fail| F[500 Error]
    E -->|Pass| G{Find Event}
    G -->|Not Found| H[404 Error]
    G -->|Found| I{Check Owner}
    I -->|Wrong Owner| J[403 Error]
    I -->|Correct| K{Delete Files}
    K -->|Error| L[Log Warning, Continue]
    K -->|Success| M{Update JSON}
    M -->|Error| N[500 Error]
    M -->|Success| O[200 Success]
    
    D --> P[Return Error Response]
    F --> P
    H --> P
    J --> P
    N --> P
    O --> Q[Return Success Response]
    
    style D fill:#ff6b6b
    style F fill:#ff6b6b
    style H fill:#ffa500
    style J fill:#ff6b6b
    style L fill:#ffd93d
    style N fill:#ff6b6b
    style O fill:#6bcf7f
```

## 🔄 State Transitions

```
Initial State: Event Exists
├── User Action: Click Delete
│   └── State: Modal Open
│       ├── User Action: Click Cancel
│       │   └── State: Event Exists (no change)
│       └── User Action: Click Confirm
│           └── State: Deleting
│               ├── API Success
│               │   └── State: Event Deleted
│               │       └── UI State: Event Removed
│               └── API Error
│                   └── State: Event Exists (with error)
│                       └── UI State: Error Shown
```

---

*Diagram created: December 13, 2024*
*Implementation: Complete ✅*
