# WorkTrack Pro (DEGHA NOVA) - Enterprise KPI & Workforce Management System

An enterprise-grade, multi-role workforce performance management, task workflow, dynamic localization, real-time messaging, and KPI analytics platform built on **Django**, **Django REST Framework**, **Celery**, and **Vanilla JS / Modern CSS**.

---

## 🌟 Executive System Overview

WorkTrack Pro provides organizations with end-to-end operational governance. Designed to deploy seamlessly in multi-tenant or single-tenant production environments (including cPanel/Passenger WSGI subpath setups like `/cnrst`), the platform automates task distribution, submission versioning, dynamic translation, real-time messaging with embedded voice equalizer widgets, and automatic multi-weighted KPI calculation.

---

## 🛠️ Technology Stack

| Layer | Technologies & Frameworks |
| :--- | :--- |
| **Backend Core** | Python 3.13, Django 5.x, Django REST Framework (DRF), SimpleJWT |
| **Database Support** | MySQL (PyMySQL), PostgreSQL (`psycopg2`), SQLite (Local Dev) |
| **Asynchronous Engine** | Celery 5.x, Redis, Django-Celery-Beat |
| **Frontend & UI** | Vanilla JS (ES6+), Bootstrap 5, FontAwesome, SweetAlert2, HTML5 Canvas Equalizers |
| **Localization** | `DynamicTranslationMiddleware`, Google Free Translate Engine API |
| **Asset Pipeline** | WhiteNoise Static Storage, HTML Canvas Waveforms, HTML Audio APIs |
| **Production WSGI** | Phusion Passenger, Gunicorn, Nginx / Apache Reverse Proxies |

---

## 🏗️ High-Level System Architecture

```mermaid
graph TD
    Client[Browser Client / Web Dashboard] --> |HTTPS / WSS| ReverseProxy[cPanel Apache / Nginx Proxy]
    ReverseProxy --> |HTTP + X-Forwarded Headers| WSGI[Passenger WSGI / Gunicorn]
    
    subgraph Django Core Backend
        WSGI --> URLConf[URL Router / Subpath /cnrst]
        URLConf --> DynHostMW[DynamicHostMiddleware]
        DynHostMW --> AuthMW[Authentication & Session Middleware]
        AuthMW --> DynTransMW[DynamicTranslationMiddleware]
        DynTransMW --> Views[Views & DRF Viewsets]
        Views --> ORM[Django ORM]
    end

    subgraph Data & Storage Layer
        ORM --> RDBMS[(MySQL / PostgreSQL / SQLite)]
        ORM --> MediaStorage[Local Media / Attachments Storage]
    end

    subgraph Async & Background Workers
        Views --> |Tasks / Email Queue| Celery[Celery Async Workers]
        Celery --> Redis[(Redis Broker)]
        Celery --> SMTPServer[SMTP Mail Server]
    end
```

---

## 📋 Comprehensive Feature Modules

### 1. User Command Center & Management
- **Role-Based Access Control (RBAC)**: Super Admin, Manager, and Worker tiers.
- **Atomic Deletion & Soft-Deactivation**: Safe account removal wrapped in `transaction.atomic()` savepoints. If linked records exist (`Task`, `Submission`, `ActivityLog`), the system falls back to `is_active=False` soft deactivation without breaking database constraints.
- **Subpath Cookie Isolation**: Custom cookie naming (`cnrst_sessionid`, `cnrst_csrftoken`) with `credentials: 'same-origin'` for cPanel subpath deployment.

### 2. Task Management, Kanban & Calendar
- **Full Task Lifecycle**: Creation, priority scoring, tag assignment, worker allocation, and cover/attachment management.
- **Interactive Views**: Standard table view, drag-and-drop Kanban board, and monthly calendar schedule.
- **Bulk Operations**: Multi-task assignment, status updating, and CSV exporting.

### 3. Submission Engine & Version Control
- **File Attachments & Comments**: Multi-version task submissions with interactive document preview.
- **Review & Approval**: Manager feedback loops, rating assignments, and on-time status tagging.

### 4. Automated KPI Engine
- **Multi-Factor Formula**:
  $$\text{KPI Score} = (0.25 \times \text{Completion}) + (0.25 \times \text{OnTime}) + (0.30 \times \text{Quality}) + (0.20 \times \text{Productivity})$$
- **Recalculation Pipeline**: Automatic weight configuration and batch history calculation.

### 5. Messenger & Glassmorphic Voice Interface
- **Real-Time Communication**: Group and 1-on-1 instant messaging with interactive polling.
- **Voice Message Studio**: Glassmorphism recording bar featuring dynamic green HTML5 canvas audio equalizer and custom seekable voice player widgets (1x / 1.5x / 2x speed controls).

### 6. Dynamic Localization Engine
- **Bilingual Interface (EN / AR)**: Auto-translates template rendered strings on-the-fly via `DynamicTranslationMiddleware`.
- **RTL / LTR Support**: Instant switching of directionality and language state.

---

## 🔄 System Workflows & Sequence Diagrams

### Workflow 1: User Management & Safe Deletion Workflow

```mermaid
sequenceDiagram
    autonumber
    actor Admin as Super Admin / Manager
    participant JS as Frontend JS (admin_users.html)
    participant Django as Django Backend (user_delete)
    participant DB as Relational Database (MySQL)

    Admin->>JS: Click "Delete User" button
    JS->>Admin: Display SweetAlert Confirmation Modal
    Admin->>JS: Confirm Deletion
    JS->>JS: Resolve subpath URL {% url 'user-delete' id %}
    JS->>Django: POST /cnrst/management/users/{id}/delete/ (credentials: same-origin)
    
    alt Unauthenticated Session
        Django-->>JS: HTTP 401 JSON {status: 'error', message: 'Session required'}
        JS-->>Admin: Show "Session Required" Modal
    else Authorized Request
        Django->>DB: Begin transaction.atomic() savepoint
        Django->>DB: Attempt hard delete user.delete()
        
        alt Success (No Foreign Keys)
            DB-->>Django: Hard deletion complete
            Django-->>JS: HTTP 200 JSON {status: 'success', message: 'User deleted'}
            JS-->>Admin: Show Success Toast & Reload Page
        else Constraint Failure (Linked Tasks/Logs)
            DB-->>Django: Raise IntegrityError / ProtectedError
            Django->>DB: Rollback savepoint cleanly
            Django->>DB: Execute User.objects.filter(id).update(is_active=False)
            DB-->>Django: User set to inactive
            Django-->>JS: HTTP 200 JSON {status: 'success', deactivated: true}
            JS-->>Admin: Show Warning Toast "User deactivated due to linked records"
        end
    end
```

---

### Workflow 2: Task Submission Lifecycle & KPI Scoring

```mermaid
sequenceDiagram
    autonumber
    actor Worker
    actor Manager
    participant Web as Web Dashboard
    participant API as Submission API View
    participant DB as Database
    participant KPI as KPI Calculation Engine

    Worker->>Web: Upload Task File & Submit Work
    Web->>API: POST /api/submissions/ (Task ID, File, Notes)
    API->>DB: Create Submission record (Version N)
    API->>DB: Update Task status to "UNDER_REVIEW"
    API-->>Web: Submission Successful
    
    Manager->>Web: Open Manager Review Dashboard
    Manager->>Web: Assign Quality Score (1-100) & Approve
    Web->>API: POST /api/submissions/{id}/review/ (status=APPROVED, score=95)
    API->>DB: Update Submission & Task status to "COMPLETED"
    API->>KPI: Trigger recalculate_user_kpi(worker_id)
    KPI->>DB: Query monthly completed tasks, on-time rate, and quality score
    KPI->>KPI: Apply formula (0.25*Comp + 0.25*OnTime + 0.30*Qual + 0.20*Prod)
    KPI->>DB: Save UserKPI record
    API-->>Web: Review saved & KPI updated
```

---

### Workflow 3: Voice Message Recording & Equalizer Playback

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant UI as Messenger UI
    participant AudioAPI as Browser MediaRecorder API
    participant Server as Messaging API View
    participant Storage as Media File Storage

    User->>UI: Press & Hold Voice Record Button
    UI->>AudioAPI: MediaDevices.getUserMedia({ audio: true })
    AudioAPI-->>UI: Audio Stream Stream
    UI->>UI: Draw real-time green equalizer canvas animation
    User->>UI: Release Record / Send Button
    UI->>AudioAPI: stop() & compile Blob (audio/webm or audio/mp3)
    UI->>Server: POST /messenger/api/send-voice/ (FormData + Audio Blob)
    Server->>Storage: Save audio file to /media/voice_messages/
    Server->>Server: Create Message record (is_voice=True)
    Server-->>UI: Return JSON Message object with audio_url
    UI->>UI: Render custom voice widget (Waveform, Seekbar, Speed Control)
```

---

### Workflow 4: Dynamic Subpath Localization Middleware

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant MW as DynamicTranslationMiddleware
    participant View as Django Template View
    participant TransEngine as Google Translation Engine API

    User->>MW: Request GET /cnrst/management/users/ (Cookie: django_language=ar)
    MW->>View: Pass request downstream
    View-->>MW: Return rendered English HTML response
    MW->>MW: Intercept HTML content-type response
    MW->>MW: Extract translatable text strings
    MW->>TransEngine: Translate extracted strings (EN -> AR)
    TransEngine-->>MW: Return translated Arabic strings
    MW->>MW: Inject Arabic text & set dir="rtl" attribute
    MW-->>User: Return fully translated Arabic HTML page
```

---

## 🚀 Production cPanel Deployment Guide

### 1. Reverse Proxy SSL Header Configuration (`settings.py`)
Ensure your `settings.py` includes reverse proxy SSL headers for cPanel's Apache/Nginx to Passenger proxying:
```python
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
```

### 2. Cookie Isolation for Subpath (`/cnrst/`)
When deploying under a subpath like `https://dhetasks.com/cnrst`:
```python
FORCE_SCRIPT_NAME = '/cnrst'
SESSION_COOKIE_PATH = '/cnrst/'
CSRF_COOKIE_PATH = '/cnrst/'
SESSION_COOKIE_NAME = 'cnrst_sessionid'
CSRF_COOKIE_NAME = 'cnrst_csrftoken'
```

### 3. SMTP Email Configuration
- **Port 465 (Implicit SSL)**:
  ```ini
  EMAIL_PORT=465
  EMAIL_USE_SSL=True
  EMAIL_USE_TLS=False
  ```
- **Port 587 (STARTTLS)**:
  ```ini
  EMAIL_PORT=587
  EMAIL_USE_TLS=True
  EMAIL_USE_SSL=False
  ```

---

## 📁 Project Directory Structure

```
DEGHA NOVA/
├── docs/                   # Complete project documentation, guides, and reports
│   ├── DOCUMENTATION_INDEX.md # Master documentation index
│   ├── guides/             # User, developer, API, and setup guides
│   ├── reports/            # System audits, milestone reports, and completion summaries
│   └── prototypes/         # HTML design prototypes and mockups
├── scripts/                # Project automation, database, and maintenance scripts
│   ├── database/           # DB seed scripts, demo data, and translation tools
│   ├── maintenance/        # UI/CSS patches, template repairs, and maintenance tools
│   ├── deployment/         # Server deployment, cPanel, macOS, and update scripts
│   └── utils/              # Verification utilities and asset helpers
├── tests/                  # Automated test suite and test verification scripts
├── backup/                 # Database backups and configuration snapshots
├── logs/                   # Server logs, test outputs, and worker logs
├── tmp/                    # Temporary rendering and scratch files
├── comit/                  # Feature planning and architectural design logs
├── worktrack_pro/          # Django core project configuration (settings, urls, wsgi)
├── worktrack-pro/          # Frontend application workspace
├── [apps]/                 # Django apps (users, tasks, submissions, kpi, etc.)
├── static/ & media/        # Static assets and uploaded media files
├── manage.py & manage.sh   # Main Django CLI and interactive management scripts
├── menu.sh                 # Quick interactive menu runner
├── activate.sh             # System security activation & environment script
└── requirements.txt        # Python dependency manifest
```

---

## 💻 Local Development Setup

```bash
# Clone project and navigate to folder
cd "DEGHA NOVA"

# Create virtual environment & activate
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations & check system
python manage.py check
python manage.py migrate

# Start development server
python manage.py runserver 0.0.0.0:8000
```

---

**WorkTrack Pro (DEGHA NOVA)** — Built for Enterprise Excellence.
