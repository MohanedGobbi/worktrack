#!/bin/bash
# QUICKSTART.sh - WorkTrack Pro Quick Start Guide

cat << 'EOF'

╔════════════════════════════════════════════════════════════════════╗
║                  WorkTrack Pro - Quick Start Guide                ║
║                                                                    ║
║          Full GUI Web Application - Ready to Test! 🚀             ║
╚════════════════════════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📖 TABLE OF CONTENTS:

  1. How to Start the Server
  2. How to Login
  3. Test Account Credentials
  4. Key Pages to Explore
  5. What's New (GUI Transformation)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1️⃣  HOW TO START THE SERVER

  From the project root (/home/pc-2026-1/Desktop/TODO/worktrack_pro):

    $ source venv/bin/activate
    $ python manage.py runserver 0.0.0.0:8000

  Then visit: http://localhost:8000

  ✅ Server Status: Currently Running!
  ✅ Database: SQLite (db.sqlite3) - Fresh and Ready

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

2️⃣  HOW TO LOGIN

  Go to: http://localhost:8000/login/

  Enter Email and Password from the test accounts below.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

3️⃣  TEST ACCOUNT CREDENTIALS

  ┌─────────────────────────────────────────────────────────────────┐
  │ ADMIN (Full System Access)                                      │
  ├─────────────────────────────────────────────────────────────────┤
  │ Email:    admin@worktrack.local                                 │
  │ Password: Admin@123456                                          │
  └─────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────┐
  │ MANAGER (Can Create Tasks & Review Submissions)                 │
  ├─────────────────────────────────────────────────────────────────┤
  │ Email:    manager@worktrack.local                               │
  │ Password: Manager@123456                                        │
  └─────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────┐
  │ WORKER #1 (Alice Smith)                                         │
  ├─────────────────────────────────────────────────────────────────┤
  │ Email:    worker1@worktrack.local                               │
  │ Password: Worker@123456                                         │
  └─────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────┐
  │ WORKER #2 (Bob Jones)                                           │
  ├─────────────────────────────────────────────────────────────────┤
  │ Email:    worker2@worktrack.local                               │
  │ Password: Worker@123456                                         │
  └─────────────────────────────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

4️⃣  KEY PAGES TO EXPLORE

  ✨ HOME PAGE
    →  http://localhost:8000
    →  Landing page showcasing features
    →  Free to browse without login

  🔐 AUTHENTICATION
    →  http://localhost:8000/login/       (Login form)
    →  http://localhost:8000/register/    (Create account)
    →  http://localhost:8000/logout/      (Logout)

  📊 DASHBOARD (Requires Login)
    →  http://localhost:8000/dashboard/
    →  Shows your stats, tasks, submissions
    →  Personalized based on your role

  ✅ TASKS
    →  http://localhost:8000/tasks/
    →  View assigned tasks (workers)
    →  Create & manage tasks (managers)
    →  Filter by status, priority, search
    →  View task details, edit, delete

  📥 SUBMISSIONS
    →  http://localhost:8000/submissions/
    →  Submit completed work
    →  Managers can review & approve/reject
    →  Add comments during review

  🔔 NOTIFICATIONS
    →  http://localhost:8000/notifications/
    →  All notifications in one place
    →  Mark as read/unread
    →  Filter and manage alerts

  👤 PROFILE
    →  http://localhost:8000/profile/
    →  Update personal information
    →  Change password
    →  Set preferences (notifications, theme)
    →  View login history

  ⚙️  ADMIN DASHBOARD (Admin/Manager Only)
    →  http://localhost:8000/admin-dashboard/
    →  System statistics
    →  User management
    →  Performance analytics

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

5️⃣  WHAT'S NEW (GUI TRANSFORMATION)

  🎉 FULLY FUNCTIONAL WEB GUI (Previously REST API Only)

  ✨ Features Implemented:
    ✅ Beautiful Bootstrap 5 UI with responsive design
    ✅ Gradient purple theme (#667eea → #764ba2)
    ✅ 15+ professional HTML templates
    ✅ 23 view functions for all CRUD operations
    ✅ Complete user authentication system
    ✅ Role-based access control
    ✅ Task management with filtering
    ✅ Submission workflow with approvals
    ✅ Notification system
    ✅ User profile & settings management
    ✅ Admin dashboard with analytics
    ✅ Mobile-responsive design
    ✅ Form validation & error handling
    ✅ CSRF protection on all forms
    ✅ Custom 404 & 500 error pages

  🎨 Design Highlights:
    • Gradient navbar with user menu
    • Responsive stat cards with animations
    • Professional badges for status indicators
    • Clean form layouts with icons
    • Hover effects and transitions
    • Mobile-first approach
    • Accessibility standards

  📱 Fully Responsive:
    • Mobile phones (< 576px)
    • Tablets (768px - 991px)
    • Desktops (992px+)
    • All pages work on all screen sizes

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🧪 TESTING WORKFLOWS

  Try This:

  1. REGISTER A NEW ACCOUNT
     → Visit /register/
     → Create your own account
     → Login with your credentials

  2. MANAGER CREATES TASK
     → Login as: manager@worktrack.local / Manager@123456
     → Go to Tasks → Create Task
     → Assign to: worker1@worktrack.local
     → Set deadline and priority

  3. WORKER COMPLETES TASK
     → Login as: worker1@worktrack.local / Worker@123456
     → View dashboard (see assigned task)
     → Go to Tasks to view details
     → Submit work via Submissions

  4. MANAGER REVIEWS
     → Login as: manager@worktrack.local
     → Go to Submissions
     → Review submitted work
     → Approve or Reject with comments

  5. CHECK NOTIFICATIONS
     → Login as: worker1@worktrack.local
     → Go to Notifications
     → See approval status notification
     → Mark as read

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📚 USEFUL FILES

  TESTING_GUIDE.md
    → Comprehensive testing documentation
    → Detailed workflow examples
    → Feature checklist
    → Troubleshooting tips

  GUI_IMPLEMENTATION_SUMMARY.md
    → Overview of all implemented pages
    → Complete feature list
    → Technical specifications
    → Deployment notes

  core/template_views.py
    → All view functions (23 total)
    → Business logic
    → Database queries

  templates/
    → All HTML templates (15 pages)
    → Bootstrap 5 layouts
    → Form validations

  worktrack_pro/urls.py
    → All URL routes (30+)
    → RESTful URL structure

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💬 QUICK TIPS

  • All passwords are case-sensitive
  • Account creation checks password strength (8+ chars)
  • Managers can see all tasks; Workers only see assigned
  • Notifications appear real-time on actions
  • Filter tasks by status: Pending, In Progress, Completed
  • Set task priority: Low, Medium, High
  • Manager-only features appear in task/submission lists
  • Profile password change requires current password
  • All forms have CSRF protection enabled
  • Admin panel available at /admin/ with Django interface

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚀 READY TO GO!

  The application is fully functional and ready for testing.
  
  Start the server, login with any test account, and explore!

  Questions? Check TESTING_GUIDE.md for detailed documentation.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EOF

echo ""
echo "✨ WorkTrack Pro is ready! Visit: http://localhost:8000"
echo ""
