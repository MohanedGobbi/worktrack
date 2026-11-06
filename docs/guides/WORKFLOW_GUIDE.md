# Task Submission Workflow Guide

## Overview
This document describes the complete task submission workflow in WorkTrack Pro, from task creation to review completion.

## Workflow Stages

### Stage 1: Task Creation (Manager/Super Admin)

**Who:** Manager or Super Admin
**What:** Create a task and assign it to one or more workers

**Steps:**
1. Navigate to **Tasks** → **Create Task**
2. Fill in task details:
   - Task Title
   - Description
   - Deadline
   - Priority
3. Assign workers by selecting from dropdown (multiple selection possible)
4. Click **Create Task**
5. Task status automatically set to **Pending**

**Result:** Task appears in assigned workers' dashboards

---

### Stage 2: Worker Views Task (Worker)

**Who:** Assigned worker
**What:** View assigned task details and create submission

**Steps:**
1. Login as worker
2. Go to **Dashboard** - see assigned tasks
3. Click on the task to view details
4. View task information, deadline, and requirements
5. Click **Create Submission** button

**Result:** Draft submission created

---

### Stage 3: Worker Creates Draft Submission (Worker)

**Who:** Assigned worker
**What:** Create initial draft submission

**Steps:**
1. System redirects to submission creation form
2. Worker enters submission details:
   - Select task (pre-filled if coming from task detail)
   - Add notes/description
   - Upload file (optional)
3. Click **Create Submission**
4. Submission status set to **Draft** (blue badge)

**Result:** Draft submission created, worker can edit it

---

### Stage 4: Worker Edits Draft Submission (Worker)

**Who:** Assigned worker
**What:** Edit and refine draft submission before submitting

**Steps:**
1. Navigate to **Submissions** or click on the submission
2. View submission detail page
3. See **Draft Actions** section with:
   - **Continue Editing** button
   - **Submit for Review** button
4. Click **Continue Editing** to modify:
   - Notes/description
   - Upload new file
   - Update submission content
5. Make changes and save

**Result:** Draft submission updated, changes reflected immediately

---

### Stage 5: Worker Submits Submission (Worker)

**Who:** Assigned worker
**What:** Submit draft for manager review

**Steps:**
1. Navigate to draft submission
2. Review all details to ensure correct
3. Scroll to **Draft Actions** section
4. Click **Submit for Review** button
5. System changes status to **Submitted** (blue bagde)
6. Task status automatically updated to **Submitted**
7. Notification sent to all managers

**Result:** Submission moved to manager queue for review

---

### Stage 6: Manager Reviews Submission (Manager/Super Admin)

**Who:** Manager or Super Admin
**What:** Review submitted work and provide feedback

**Steps:**
1. Login as manager
2. View **Notifications** - see "New Submission" notifications
3. Navigate to **Submissions** → view submitted items
4. Click on submission to open detail page
5. Review:
   - Submitted content/file
   - Submit time
   - Worker information
6. Form appears with **Manager Review** section
7. Optionally enter:
   - Review Feedback (text field)
   - Score (0-100)

**Result:** Ready to approve or reject

---

### Stage 7: Manager Approves or Rejects (Manager/Super Admin)

**Who:** Manager or Super Admin
**What:** Approve or reject the submitted work

**Approve Workflow:**
1. Click **Approve** button in Manager Review section
2. System updates submission status to **Approved** (green badge)
3. Task status updated to **Approved**
4. Feedback and score (if entered) saved to submission
5. Worker notification sent (approval completed)

**Reject Workflow:**
1. Click **Reject** button in Manager Review section
2. Enter rejection reason when prompted
3. System updates submission status to **Rejected** (red badge)
4. Reason saved as manager feedback
5. Worker can re-edit and resubmit

**Result:** Submission review complete

---

## Status Flow Diagram

```
Task Creation (Pending)
        ↓
Task Assigned to Workers
        ↓
Worker Creates Submission → Status: Draft
        ↓
    [WORKER EDIT LOOP]
        ↓
Worker Submits for Review → Status: Submitted, Notification to Manager
        ↓
Manager Reviews → Status: Under Review
        ↓
    [DECISION POINT]
    ↙                    ↘
Approve              Reject
  ↓                    ↓
Approved           Can Resubmit
Status: ✓           (back to draft)
```

---

## Key Features

### Draft Workflow
- **Status:** Draft (blue badge with pencil icon)
- **Editable:** Yes - continue editing
- **Visible to:** Worker who created it + Managers
- **Can Submit:** Yes - changes to Submitted status

### Submitted Workflow
- **Status:** Submitted (blue badge with paper plane icon)
- **Editable:** No - awaiting review
- **Visible to:** Worker + Managers
- **Can Edit:** No - manager must review first

### Under Review Workflow
- **Status:** Under Review (yellow badge with hourglass icon)
- **Editable:** No
- **Manager Can:** Add feedback, score, approve, or reject
- **Time:** No deadline for manager review

### Final States
- **Approved:** Green badge, work accepted
- **Rejected:** Red badge, worker can edit and resubmit if rejected

---

## Permissions Summary

| Action | Worker | Manager | Super Admin |
|--------|--------|---------|------------|
| Create Task | ✗ | ✓ | ✓ |
| Assign Task | ✗ | ✓ | ✓ |
| Create Submission | ✓* | ✓* | ✓* |
| View Own Submission | ✓ | ✓ (all) | ✓ (all) |
| Edit Draft | ✓ | ✓ (all) | ✓ (all) |
| Submit Submission | ✓ | ✓ | ✓ |
| Review Submission | ✗ | ✓ | ✓ |
| Approve/Reject | ✗ | ✓ | ✓ |

*Only for tasks assigned to them

---

## Notifications

### For Workers:
- Task assigned to you
- Submission approved
- Submission rejected (with feedback)

### For Managers:
- New submission received
- Submission status changed
- Task deadline approaching

---

## Status Codes Explained

| Status | Badge Color | Icon | Meaning |
|--------|------------|------|---------|
| Draft | 🔵 Blue | ✏️ | Work in progress, editable |
| Submitted | 🔵 Blue | ✈️ | Waiting for manager review |
| Under Review | 🟡 Yellow | ⏳ | Manager is reviewing |
| Approved | 🟢 Green | ✓ | Work accepted |
| Rejected | 🔴 Red | ✗ | Work needs revision |

---

## Common Scenarios

### Scenario 1: Worker Loses Internet Before Submit
- Draft is auto-saved
- Can continue editing when reconnected
- No time pressure

### Scenario 2: Manager Needs More Info
- Reject with detailed feedback
- Worker re-edits with feedback
- Resubmits for review

### Scenario 3: Multiple Workers on Same Task
- Each worker has their own submission
- Manager reviews all individually
- Can approve one, reject another

### Scenario 4: Resubmission After Rejection
1. Worker views rejected submission (red badge)
2. Clicks "Continue Editing"
3. Reviews manager feedback
4. Makes corrections
5. Increases version number automatically
6. Resubmits

---

## Tips for Best Experience

### For Workers:
1. **Save Often:** Use "Continue Editing" to save changes
2. **Review Before Submit:** Check everything before clicking "Submit for Review"
3. **Pay Attention to Feedback:** Manager feedback helps improve quality
4. **Meet Deadlines:** Try to submit before task deadline

### For Managers:
1. **Review Promptly:** Don't leave submissions pending too long
2. **Be Specific with Feedback:** Clear feedback helps workers improve
3. **Use Scoring:** Helps track performance over time
4. **Batch Reviews:** Set aside time to review all pending submissions

---

## Troubleshooting

### "I Can't See the Task"
- Check if you're logged in as the correct user
- Check if task is assigned to your user account
- Verify task status is "Pending" or "In Progress"

### "Submit Button is Disabled"
- Check submission status - only drafts can be submitted
- Verify you are the submission worker
- Try refreshing the page

### "Can't Edit Submission"
- Only draft submissions are editable
- Once submitted, only managers can request changes
- If rejected, you can edit and resubmit

### "Feedback Not Showing"
- Refresh the page
- Check if you're viewing the correct submission
- Verify status is "Approved" or "Rejected"

---

## API Endpoints (For Developers)

### Submission Management:
- `POST /submissions/create/` - Create draft submission
- `POST /submissions/<id>/submit/` - Submit draft (worker action)
- `POST /submissions/<id>/update-status/` - Review submission (manager action)
- `GET /submissions/<id>/` - View submission details
- `POST /submissions/<id>/edit/` - Edit draft submission

### Task Management:
- `GET /tasks/` - List all tasks
- `GET /tasks/<id>/` - View task details
- `POST /tasks/create/` - Create task (manager only)
- `POST /tasks/<id>/edit/` - Edit task (manager only)

### Notifications:
- `GET /notifications/` - List notifications
- `POST /notifications/<id>/mark-as-read/` - Mark as read

---

**Last Updated:** February 24, 2026
**Version:** 1.0
**Status:** Production Ready ✓
