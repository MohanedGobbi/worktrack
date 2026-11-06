# WorkTrack Pro - Testing Guide

## 🚀 Application Status

**✅ Server Running:** http://localhost:8000  
**✅ Database:** Fresh SQLite (db.sqlite3) - all tables created  
**✅ Migrations:** All applied successfully  
**✅ Test Accounts:** Created and ready to use  

---

## 📝 Test Account Credentials

### Admin/Super Admin Account
```
Email:    admin@worktrack.local
Password: Admin@123456
Role:     Super Admin (full system access)
```

### Manager Account
```
Email:    manager@worktrack.local
Password: Manager@123456
Role:     Manager (can create tasks, review submissions)
```

### Worker Account #1
```
Email:    worker1@worktrack.local
Password: Worker@123456
Role:     Worker (Alice Smith)
```

### Worker Account #2
```
Email:    worker2@worktrack.local
Password: Worker@123456
Role:     Worker (Bob Jones)
```

---

## 🧪 Testing Workflows

### Workflow 1: User Registration & Login
1. Visit: `http://localhost:8000/register/`
2. Fill in: First Name, Last Name, Email, Password (8+ chars)
3. Click "Register"
4. Go to `http://localhost:8000/login/`
5. Enter registered email and password
6. You should be redirected to `/dashboard/`

### Workflow 2: Manager Creates Task
1. Login as: **manager@worktrack.local** / **Manager@123456**
2. Go to: **Tasks** → **Create Task**
3. Fill in:
   - Title: "Complete API Documentation"
   - Description: "Write comprehensive API documentation"
   - Status: "In Progress"
   - Priority: "High"
   - Deadline: (Tomorrow's date)
   - Assign To: "Alice Smith"
4. Click "Create Task"

### Workflow 3: Worker Submits Work
1. Login as: **worker1@worktrack.local** / **Worker@123456**
2. Go to: **Dashboard** (view assigned tasks)
3. Go to: **Tasks** (should see assigned task)
4. Click task title to view details
5. Go to: **Submissions** → View your submissions
6. Submit completed work description

### Workflow 4: Manager Reviews Submission
1. Login as: **manager@worktrack.local** / **Manager@123456**
2. Go to: **Submissions**
3. Click on pending submission
4. Review the submitted work
5. Add comments and click **Approve** or **Reject**

### Workflow 5: View Notifications
1. Login as any user
2. Go to: **Notifications**
3. View unread notifications
4. Click to mark as read
5. Filter by status or type

### Workflow 6: Update Profile
1. Login as any user
2. Go to: **Profile** (top-right user menu)
3. **Account Tab:** Update name, phone, bio
4. **Security Tab:** Change password
5. **Preferences Tab:** Set notifications and theme
6. **Activity Tab:** View login history

### Workflow 7: Admin Dashboard
1. Login as: **admin@worktrack.local** / **Admin@123456**
2. Go to: **Admin Dashboard**
3. View system statistics:
   - Total users
   - Active tasks
   - Pending submissions
   - Completion rate
4. View recent users and pending reviews
5. Access management tools

---

## 🌐 Available Pages

### Public Pages (No Login Required)
- `http://localhost:8000/` - Home page with features
- `http://localhost:8000/login/` - Login page
- `http://localhost:8000/register/` - Registration page

### Authenticated Pages (Login Required)
- `http://localhost:8000/dashboard/` - User dashboard
- `http://localhost:8000/tasks/` - Task list
- `http://localhost:8000/tasks/create/` - Create task (manager only)
- `http://localhost:8000/tasks/<id>/` - Task details
- `http://localhost:8000/tasks/<id>/edit/` - Edit task (manager only)
- `http://localhost:8000/submissions/` - Submissions list
- `http://localhost:8000/submissions/<id>/` - Submission details
- `http://localhost:8000/notifications/` - Notification center
- `http://localhost:8000/profile/` - User profile settings
- `http://localhost:8000/admin-dashboard/` - Admin panel (admin/manager only)

### Admin Pages
- `http://localhost:8000/admin/` - Django admin panel
  - Username: admin@worktrack.local
  - Password: Admin@123456

---

## ✅ Features to Test

### Task Management
- [ ] Create task with deadline
- [ ] Assign task to worker
- [ ] View task details
- [ ] Edit task (change status, priority, etc)
- [ ] Filter tasks by status/priority
- [ ] Search tasks by title
- [ ] Delete task
- [ ] View task comments

### Submissions
- [ ] View assigned tasks
- [ ] Submit work for review
- [ ] View submission status
- [ ] Manager reviews and approves
- [ ] Manager rejects with feedback
- [ ] Worker sees approval status

### Notifications
- [ ] Receive notifications for task assignments
- [ ] Receive notifications for submission status
- [ ] Mark notifications as read
- [ ] Delete notifications
- [ ] Filter by type

### User Profile
- [ ] Update profile information
- [ ] Change password
- [ ] Set notification preferences
- [ ] Switch theme/language
- [ ] View login history

### Responsive Design
- [ ] Test on desktop (full width)
- [ ] Test on tablet (medium width)
- [ ] Test on mobile (narrow width)
- [ ] Check all buttons and forms responsive
- [ ] Verify navigation menu collapses on mobile

---

## 🐛 Troubleshooting

### Server not starting?
```bash
cd /home/pc-2026-1/Desktop/TODO/worktrack_pro
source venv/bin/activate
python manage.py runserver 0.0.0.0:8000
```

### Login not working?
- Verify email matches exactly (case-sensitive)
- Check password is correct (passwords are case-sensitive)
- Try creating a new account

### Pages not loading?
- Ensure server is running on port 8000
- Clear browser cache (Ctrl+Shift+Delete)
- Try in incognito/private window
- Check JavaScript console for errors (F12)

### Database issues?
```bash
# Check database status
sqlite3 db.sqlite3 ".tables"

# Reset database (delete and recreate)
rm db.sqlite3
python manage.py migrate
python manage.py shell < create_users.py
```

---

## 📊 Database Quick Info

**Database File:** `/home/pc-2026-1/Desktop/TODO/worktrack_pro/db.sqlite3`

**Tables:**
- `users_customuser` - User accounts
- `users_department` - Departments
- `tasks_task` - Tasks
- `submissions_submission` - Submissions
- `notifications_notification` - Notifications
- `kpi_userkpi` - Performance metrics
- `audit_activitylog` - Activity logs

**Create Test User Example:**
```python
# In Django shell:
from users.models import CustomUser, Department

dept = Department.objects.get(name='Engineering')
user = CustomUser.objects.create_user(
    email='test@example.com',
    password='TestPass123',
    first_name='Test',
    last_name='User',
    role='worker',
    department=dept
)
```

---

## 🎨 Design Features Tested

- ✅ Responsive Bootstrap 5 layout
- ✅ Gradient purple theme (#667eea → #764ba2)
- ✅ Navbar with user dropdown
- ✅ Message alerts (success/error/warning)
- ✅ Status badges with icons
- ✅ Form validation
- ✅ Tables with hover effects
- ✅ Cards with shadows
- ✅ Mobile-friendly navigation
- ✅ Professional typography

---

## 📋 API Endpoints (Still Available)

All REST API endpoints remain functional:

```
POST   /api/token/                    - Get JWT token
POST   /api/token/refresh/            - Refresh JWT token
GET    /api/users/                    - List users
POST   /api/users/                    - Create user
GET    /api/tasks/                    - List tasks
POST   /api/tasks/                    - Create task
GET    /api/submissions/              - List submissions
POST   /api/submissions/              - Create submission
GET    /api/notifications/            - List notifications
GET    /api/dashboards/admin_dashboard/ - Admin stats
```

---

## 💡 Tips for Testing

1. **Test in different roles:** Logout and login with different accounts to see role-based features
2. **Test complete workflows:** Create task → Assign → Submit → Review → Approve
3. **Check mobile responsiveness:** Resize browser or test on phone
4. **Test validation:** Try invalid inputs (empty fields, bad emails, weak passwords)
5. **Test permissions:** Try accessing manager pages as worker (should be denied)
6. **Test filters:** Create multiple tasks/submissions and test filters/search
7. **Check notifications:** Perform actions and verify notifications appear
8. **Test status updates:** Change task status and check dashboard updates

---

## 🔐 Security Notes

- Passwords are hashed using Django's default PBKDF2
- CSRF tokens protect all forms
- Session-based authentication for templates
- JWT available for API consumption
- User roles enforce permission boundaries
- Database queries filtered by user access level

---

**Happy Testing! 🚀**

For questions or issues, check the base.html and template_views.py files for implementation details.
