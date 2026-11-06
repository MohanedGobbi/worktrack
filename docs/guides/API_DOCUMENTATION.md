# WorkTrack Pro - API Documentation

Complete REST API reference for WorkTrack Pro workforce management system.

## Base URL
```
http://localhost:8000/api
```

## Authentication

### Obtain JWT Token
```http
POST /token/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "your_password"
}

Response (200):
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Refresh Token
```http
POST /token/refresh/
Content-Type: application/json

{
  "refresh": "your_refresh_token"
}

Response (200):
{
  "access": "new_access_token"
}
```

## Headers

All API requests (except authentication) require:
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

---

## Users Module
**Base Path**: `/api/users/`

### List Users
```http
GET /api/users/
GET /api/users/?search=email&role=manager

Query Parameters:
  - search: Search by email or name
  - page: Page number (default: 1)
  - page_size: Items per page (default: 20)
```

### Create User (Registration)
```http
POST /api/users/register/
Content-Type: application/json

{
  "email": "newuser@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "password": "SecurePass123",
  "password_confirm": "SecurePass123",
  "role": "worker"
}

Response (201):
{
  "id": 1,
  "email": "newuser@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "role": "worker",
  "created_at": "2026-02-22T10:00:00Z"
}
```

### Get Current User
```http
GET /api/users/me/

Response (200):
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "role": "manager",
  "department": {
    "id": 1,
    "name": "Engineering"
  },
  "profile": {
    "position": "Senior Engineer",
    "hire_date": "2023-01-15",
    "manager": null
  }
}
```

### Get User Details
```http
GET /api/users/{id}/

Response (200):
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "role": "manager",
  "department": 1,
  "is_active": true,
  "profile": {...},
  "created_at": "2023-01-15T00:00:00Z",
  "updated_at": "2026-02-22T10:00:00Z"
}
```

### Get Team Members (Managers Only)
```http
GET /api/users/team/

Response (200):
[
  {
    "id": 2,
    "email": "worker1@example.com",
    "first_name": "Worker",
    "last_name": "One",
    "role": "worker",
    "department": 1
  },
  ...
]
```

### List Departments (Admin Only)
```http
GET /api/users/departments/

Response (200):
[
  {
    "id": 1,
    "name": "Engineering",
    "description": "Engineering department",
    "manager": 1,
    "manager_email": "manager@example.com",
    "created_at": "2023-01-01T00:00:00Z"
  },
  ...
]
```

### Create Department (Admin Only)
```http
POST /api/users/departments/

{
  "name": "Sales",
  "description": "Sales department",
  "manager": 5
}
```

---

## Tasks Module
**Base Path**: `/api/tasks/`

### List Tasks
```http
GET /api/tasks/
GET /api/tasks/?status=pending&priority=high

Query Parameters:
  - status: pending, in_progress, submitted, approved, rejected, overdue
  - priority: low, medium, high, critical
  - page: Page number
  - ordering: -deadline, priority, -created_at
```

### Create Task (Managers Only)
```http
POST /api/tasks/

{
  "title": "Implement User Dashboard",
  "description": "Create a responsive dashboard for workers to view their tasks and KPI",
  "assigned_ids": [2, 3, 4],
  "deadline": "2026-03-15T17:00:00Z",
  "priority": "high",
  "estimated_hours": 40,
  "kpi_weight": 1.5
}

Response (201):
{
  "id": 1,
  "title": "Implement User Dashboard",
  "description": "...",
  "created_by": 1,
  "created_by_email": "manager@example.com",
  "assigned_to": [2, 3, 4],
  "assigned_to_count": 3,
  "deadline": "2026-03-15T17:00:00Z",
  "priority": "high",
  "estimated_hours": 40,
  "kpi_weight": 1.5,
  "status": "pending",
  "is_overdue": false,
  "created_at": "2026-02-22T10:00:00Z"
}
```

### Get Task Details
```http
GET /api/tasks/{id}/

Response (200):
{
  "id": 1,
  "title": "Implement User Dashboard",
  "description": "...",
  "created_by": {...},
  "assigned_to_list": [...],
  "deadline": "2026-03-15T17:00:00Z",
  "status": "in_progress",
  ...
}
```

### Assign Task to Workers (Managers Only)
```http
POST /api/tasks/{id}/assign/

{
  "worker_ids": [2, 3]
}

Response (200):
{
  "detail": "Task assigned to 2 worker(s)"
}
```

### Start Task (Workers Only)
```http
POST /api/tasks/{id}/start/

Response (200):
{
  "id": 1,
  "status": "in_progress",
  ...
}
```

---

## Submissions Module
**Base Path**: `/api/submissions/`

### List Submissions
```http
GET /api/submissions/
GET /api/submissions/?task=1&status=submitted&worker=2

Query Parameters:
  - task: Task ID
  - worker: Worker user ID
  - status: draft, submitted, under_review, approved, rejected
  - page: Page number
```

### Create Submission (Workers Only)
```http
POST /api/submissions/

{
  "task": 1,
  "file": <binary file>,
  "notes": "Completed the user dashboard with responsive design and accessibility",
  "status": "submitted"
}

Response (201):
{
  "id": 1,
  "task": 1,
  "task_title": "Implement User Dashboard",
  "worker": 2,
  "worker_email": "worker@example.com",
  "file": "/media/submissions/dashboard_final.zip",
  "notes": "Completed...",
  "status": "submitted",
  "submitted_at": "2026-02-22T14:30:00Z",
  "version": 1,
  "comments": [],
  "created_at": "2026-02-22T14:30:00Z"
}
```

### Review Submission (Managers Only)
```http
POST /api/submissions/{id}/review/

{
  "status": "approved",
  "manager_feedback": "Excellent work! Dashboard is responsive and user-friendly.",
  "score": 95
}

Response (200):
{
  "id": 1,
  "status": "approved",
  "score": 95,
  "reviewed_at": "2026-02-22T15:00:00Z",
  "manager_feedback": "Excellent work!...",
  ...
}
```

### Add Comment to Submission
```http
POST /api/submissions/{id}/comments/

{
  "comment": "Could you add a dark mode toggle?"
}

Response (201):
{
  "id": 1,
  "author": 1,
  "author_email": "manager@example.com",
  "comment": "Could you add a dark mode toggle?",
  "created_at": "2026-02-22T15:05:00Z"
}
```

---

## KPI Module
**Base Path**: `/api/kpi/`

### Get Current User's KPI
```http
GET /api/kpi/user/my_kpi/

Response (200):
{
  "id": 1,
  "user": 2,
  "user_email": "worker@example.com",
  "month": "2026-02-01",
  "month_display": "February 2026",
  "completion_rate": 85.5,
  "on_time_rate": 90.0,
  "quality_score": 88.5,
  "rejection_rate": 5.0,
  "productivity_score": 92.0,
  "total_score": 88.75,
  "calculated_at": "2026-02-22T10:00:00Z"
}
```

### Get KPI History (Last 12 Months)
```http
GET /api/kpi/user/history/

Response (200):
[
  {
    "id": ...,
    "month": "2026-02-01",
    "total_score": 88.75,
    ...
  },
  {
    "id": ...,
    "month": "2026-01-01",
    "total_score": 85.25,
    ...
  },
  ...
]
```

### List User KPIs (Admin/Manager)
```http
GET /api/kpi/user/
GET /api/kpi/user/?user=2&month=2026-02-01

Query Parameters:
  - user: User ID
  - month: Month (YYYY-MM-DD format, first day of month)
  - ordering: -month,total_score
```

### Get/Update KPI Weights (Admin Only)
```http
GET /api/kpi/weights/current/

Response (200):
{
  "completion_rate_weight": 0.25,
  "on_time_rate_weight": 0.25,
  "quality_score_weight": 0.30,
  "productivity_score_weight": 0.20,
  "updated_at": "2026-02-20T10:00:00Z"
}
```

### Update KPI Weights (Admin Only)
```http
PUT /api/kpi/weights/current/

{
  "completion_rate_weight": 0.30,
  "on_time_rate_weight": 0.25,
  "quality_score_weight": 0.25,
  "productivity_score_weight": 0.20
}

Response (200):
{updated weights}
```

### Recalculate All KPIs (Admin Only)
```http
POST /api/kpi/user/recalculate_all/

{
  "month": "2026-02-01"
}

Response (200):
{
  "detail": "Recalculated 45 KPIs",
  "data": [...]
}
```

---

## Notifications Module
**Base Path**: `/api/notifications/`

### List Notifications
```http
GET /api/notifications/
GET /api/notifications/?is_read=false&notification_type=task_assigned

Query Parameters:
  - is_read: true/false
  - notification_type: task_assigned, submission_received, etc.
```

### Mark Notification as Read
```http
POST /api/notifications/{id}/mark_read/

Response (200):
{
  "id": 1,
  "is_read": true,
  "read_at": "2026-02-22T10:30:00Z",
  ...
}
```

### Mark All Notifications as Read
```http
POST /api/notifications/mark_all_read/

Response (200):
{
  "detail": "Marked 5 notifications as read"
}
```

### Get Unread Count
```http
GET /api/notifications/unread_count/

Response (200):
{
  "unread_count": 3
}
```

### Get Notification Preferences
```http
GET /api/notifications/preferences/

Response (200):
{
  "user": 1,
  "user_email": "user@example.com",
  "email_on_task_assigned": true,
  "email_on_submission_received": true,
  "email_on_deadline_reminder": true,
  "in_app_notifications": true,
  "reminder_days_before_deadline": 1
}
```

### Update Notification Preferences
```http
PUT /api/notifications/preferences/

{
  "email_on_task_assigned": false,
  "reminder_days_before_deadline": 3
}

Response (200):
{updated preferences}
```

---

## Dashboards Module
**Base Path**: `/api/dashboards/`

### Admin Dashboard (Admin Only)
```http
GET /api/dashboards/admin_dashboard/

Response (200):
{
  "total_users": 45,
  "total_tasks": 120,
  "total_submissions": 110,
  "departments": {
    "Engineering": 88.5,
    "Sales": 82.3,
    "HR": 85.0
  },
  "task_by_status": [
    {"status": "completed", "count": 85},
    {"status": "pending", "count": 20},
    {"status": "in_progress", "count": 15}
  ],
  "top_performers": [
    {
      "user__email": "top1@example.com",
      "total_score": 95.5,
      "month": "2026-02-01"
    },
    ...
  ]
}
```

### Manager Dashboard (Managers Only)
```http
GET /api/dashboards/manager_dashboard/

Response (200):
{
  "team_members": [...],
  "total_tasks": 12,
  "pending_submissions": 3,
  "average_kpi_score": 86.5,
  "team_kpi": [...]
}
```

### Worker Dashboard
```http
GET /api/dashboards/worker_dashboard/

Response (200):
{
  "my_tasks": 5,
  "in_progress": 2,
  "completed": 3,
  "pending_review": 1,
  "my_kpi": [...]
}
```

---

## Activity Logs Module
**Base Path**: `/api/dashboards/activity-logs/`

### List Activity Logs
```http
GET /api/dashboards/activity-logs/
GET /api/dashboards/activity-logs/?action=create&object_type=Task

Query Parameters:
  - user: User ID
  - action: create, update, delete, approve, reject, assign, submit
  - object_type: Task, Submission, User, etc.
```

---

## Error Responses

All endpoints return appropriate HTTP status codes:

- **200 OK**: Successful GET, PUT, PATCH
- **201 Created**: Successful POST (resource creation)
- **204 No Content**: Successful DELETE
- **400 Bad Request**: Invalid input data
- **401 Unauthorized**: Missing or invalid authentication
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server error

### Error Response Format
```json
{
  "detail": "Error message",
  "field_name": ["Field error message"]
}
```

### Example Error Response
```json
{
  "email": ["This field must be unique."],
  "password": ["This field is required."]
}
```

---

## Pagination

List endpoints support pagination:

```http
GET /api/tasks/?page=2&page_size=50

Response Headers:
Link: <...?page=3>; rel="next", <...?page=1>; rel="previous"

Response Body:
{
  "count": 200,
  "next": "http://localhost:8000/api/tasks/?page=3",
  "previous": "http://localhost:8000/api/tasks/?page=1",
  "results": [...]
}
```

---

## Rate Limiting

- **Anonymous Users**: 100 requests/hour
- **Authenticated Users**: 1000 requests/hour

Rate limit headers returned in all responses:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1645533600
```

---

## Filtering & Searching

Many endpoints support filtering and searching:

```http
GET /api/users/?search=john&role=manager
GET /api/tasks/?status=pending&priority=high&search=dashboard
GET /api/submissions/?task=1&status=submitted
```

---

## Sorting

Most list endpoints support sorting via `ordering` parameter:

```http
GET /api/tasks/?ordering=-deadline
GET /api/kpi/user/?ordering=-total_score,-month
```

Use `-` prefix for descending order.

---

## Best Practices

1. **Always use HTTPS** in production
2. **Store tokens securely** in HTTP-only cookies or secure storage
3. **Implement token refresh** before expiration (1 hour)
4. **Handle rate limiting** gracefully with exponential backoff
5. **Validate input** on both frontend and backend
6. **Use pagination** for large datasets
7. **Cache responses** where appropriate
8. **Version your API** for backward compatibility

---

**Last Updated**: February 2026  
**API Version**: 1.0.0
