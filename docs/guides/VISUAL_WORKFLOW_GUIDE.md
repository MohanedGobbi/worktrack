# Visual Workflow Guide - Button Testing

## WORKER WORKFLOW

### Stage 1: Initial Task View (No Submission Yet)

**URL**: `http://localhost:8000/tasks/1/`

**What You Should See** ✅

```
┌─────────────────────────────────────────┐
│ TASK DETAILS                            │
│                                         │
│ Title: [Task Title]                     │
│ Description: [Task Description]         │
│                                         │
│                          ┌─────────────┐│
│                          │ CREATE      ││ ← GREEN PANEL
│                          │ SUBMISSION  ││
│                          │             ││
│                          │ [BUTTON]    ││ ← CLICK ME!
│                          │             ││
│                          │ Status:     ││
│                          │ No subm...  ││
│                          └─────────────┘│
└─────────────────────────────────────────┘
```

**Changes from Previous Session**: 
- ❌ OLD: No button visible (was hidden)
- ✅ NEW: "CREATE NEW SUBMISSION" button is VISIBLE

**Action to Take**: Click "CREATE NEW SUBMISSION" button

---

### Stage 2: Return After Creating Draft

**URL**: Same URL as above

**What You Should See** ✅

```
┌─────────────────────────────────────────┐
│ TASK DETAILS                            │
│                                         │
│                          ┌─────────────┐│
│                          │ CREATE      ││ ← GREEN PANEL
│                          │ SUBMISSION  ││
│                          │             ││
│                          │ [BLUE BTN]  ││ ← DIFFERENT BUTTON!
│                          │ CONTINUE    ││
│                          │ EDITING     ││
│                          │ DRAFT       ││
│                          │             ││
│                          │ [VIEW] [X]  ││ ← Status details
│                          │             ││
│                          │ Status:     ││
│                          │ Draft       ││
│                          └─────────────┘│
└─────────────────────────────────────────┘
```

**Changes from Previous Session**: 
- ❌ OLD: Button disappeared after creating draft
- ✅ NEW: "CONTINUE EDITING DRAFT" button is VISIBLE

**Action to Take**: Click "CONTINUE EDITING DRAFT" to edit submission

---

### Stage 3: Submission Detail Page (Draft Status)

**URL**: `http://localhost:8000/submissions/2/`

**What You Should See** ✅

```
┌──────────────────────────────────────────────────────────┐
│ SUBMISSION DETAIL                                        │
│                                                          │
│ Status: [DRAFT]                  Version 1               │
│ Submitted: Not yet submitted                             │
│                                                          │
│ ┌────────────────────────────────────────────────────┐  │
│ │ DRAFT ACTIONS - Edit or Submit        ← BLUE PANEL│  │
│ │                                                    │  │
│ │ You can continue editing or submit for review     │  │
│ │                                                    │  │
│ │ [EDIT SUBMISSION]                                 │  │
│ │ [SUBMIT FOR REVIEW] ← Click to send to manager    │  │
│ └────────────────────────────────────────────────────┘  │
│                                                          │
│ ┌────────────────────────────────────────────────────┐  │
│ │ YOUR SUBMISSION STATUS                             │  │
│ │                                                    │  │
│ │ ◉─→ Submission Created   [Date/Time]             │  │
│ │ ◎─→ Awaiting Submission  Pending...              │  │
│ │ ○─→ (Grayed out - future status)                 │  │
│ └────────────────────────────────────────────────────┘  │
│                                                          │
│ [File/Content Viewer Below]                            │
└──────────────────────────────────────────────────────────┘
```

**Changes from Previous Session**: 
- ❌ OLD: No visible button to submit
- ✅ NEW: "SUBMIT FOR REVIEW" button is VISIBLE and prominent

**Action to Take**: Click "SUBMIT FOR REVIEW" button

---

## MANAGER WORKFLOW

### Stage 1: After Worker Submits (CRITICAL FIX)

**URL**: `http://localhost:8000/submissions/2/` (viewed as manager)

**What You Should See** ✅

```
┌──────────────────────────────────────────────────────────┐
│ SUBMISSION DETAIL (Manager View)                         │
│                                                          │
│ Status: [SUBMITTED] ← KEY: Status is "submitted"        │
│                                                          │
│ ┌────────────────────────────────────────────────────┐  │
│ │ MANAGER REVIEW - Approve or Reject   ← YELLOW!    │  │
│ │                                                    │  │
│ │ 💡 Instructions: Review, add feedback, approve   │  │
│ │    or reject                                       │  │
│ │                                                    │  │
│ │ Your Feedback (Optional)                          │  │
│ │ [════════════════════════════════════════════════] │  │
│ │ |  Enter your review here...                      │  │
│ │ |                                                 │  │
│ │ └─────────────────────────────────────────────────┤  │
│ │                                                    │  │
│ │ Score (Optional, 0-100)                           │  │
│ │ [___] / 100                                        │  │
│ │                                                    │  │
│ │ [✓ APPROVE SUBMISSION] ← Click to approve         │  │
│ │ [✗ REJECT SUBMISSION]  ← Click to reject          │  │
│ └────────────────────────────────────────────────────┘  │
│                                                          │
│ [Submission Details & File Viewer Below]               │
└──────────────────────────────────────────────────────────┘
```

**Changes from Previous Session**: 
- ❌ OLD: Review panel NOT VISIBLE when status = "submitted"
- ❌ OLD: Manager had to wait for status to change to "under_review"
- ✅ NEW: Review panel VISIBLE immediately when status = "submitted"

**Action to Take**: 
1. Add feedback (optional)
2. Add score (optional)
3. Click "APPROVE SUBMISSION" or "REJECT SUBMISSION"

---

### Stage 2: After Manager Approval

**What You Should See** ✅

```
┌──────────────────────────────────────────────────────────┐
│ SUBMISSION DETAIL                                        │
│                                                          │
│ Status: [APPROVED] ← Status changed                      │
│ Reviewed: [Date/Time]                                    │
│ Score: 85/100                                            │
│                                                          │
│ ┌────────────────────────────────────────────────────┐  │
│ │ ✓ REVIEW DECISION - APPROVED                       │  │
│ │                                                    │  │
│ │ Reviewer: manager@worktrack.local                 │  │
│ │ Feedback: [Manager's feedback text]               │  │
│ │ Score: 85/100                                      │  │
│ │                                                    │  │
│ │ Review Date: [Timestamp]                          │  │
│ └────────────────────────────────────────────────────┘  │
│                                                          │
│ [Manager Review Panel is now HIDDEN - read-only]        │
└──────────────────────────────────────────────────────────┘
```

**If Rejected**:
```
│ Status: [REJECTED]                                       │
│                                                          │
│ ┌────────────────────────────────────────────────────┐  │
│ │ ✗ REVIEW DECISION - REJECTED                       │  │
│ │                                                    │  │
│ │ Reviewer: manager@worktrack.local                 │  │
│ │ Feedback: [Reason for rejection]                  │  │
│ │ Score: 45/100                                      │  │
│ └────────────────────────────────────────────────────┘  │
```

---

## Complete Status Transitions

### Before Fix ❌
```
Task Page (Worker):
  No submission → [NO BUTTON - BROKEN] → Create submission → [BUTTON DISAPPEARS - BROKEN]

Submission Page (Manager):
  Status = "submitted" → [REVIEW PANEL NOT VISIBLE - BROKEN]
  Wait for status change...
  Status = "under_review" → [FINALLY CAN REVIEW]
```

### After Fix ✅
```
Task Page (Worker):
  No submission → [CREATE BUTTON ✓] → Create → [CONTINUE EDITING ✓] 

Submission Page (Manager):
  Status = "submitted" → [CAN REVIEW IMMEDIATELY ✓]
  Add feedback → [APPROVE/REJECT ✓]
  Status changes automatically → Workflow complete ✓
```

---

## Button Style Reference

### Color Codes
- **Green (`btn-success`)**: Primary actions - Create, Approve
- **Blue (`btn-primary`)**: Edit/Update actions - Continue Editing, Save Changes
- **Yellow/Warning (`border-warning`)**: Attention needed - Review Panel header
- **Red (`btn-danger`)**: Destructive actions - Reject, Delete

### Icon Reference
- 📁 `fas fa-file-upload` - Create submission
- ✏️ `fas fa-edit` - Edit submission
- ✓ `fas fa-check-circle` - Approve
- ✗ `fas fa-times-circle` - Reject
- 📄 `fas fa-file-alt` - View file
- 🗑️ `fas fa-trash` - Delete

---

## Troubleshooting Visual Checklist

### If you see "Create New Submission" button everywhere
✓ Worker panel is now correctly showing for all workers
✓ This is NOT a bug - it's the fix
✓ Button text changes based on submission status (intended behavior)

### If you don't see the Manager Review Panel
- [ ] Are you logged in as a manager? (check email: manager@worktrack.local)
- [ ] Is the submission status showing "submitted" or "under_review"?
- [ ] Did you create the submission as a different worker?
- [ ] Clear browser cache (Ctrl+Shift+Delete) and refresh

### If buttons don't respond when clicked
- [ ] Check browser console (F12) for JavaScript errors
- [ ] Make sure form fields are filled (especially file upload)
- [ ] Try a different browser (Chrome, Firefox, Safari)
- [ ] Check Django server logs (terminal where server is running)

---

## Feature Checklist - What Should Now Work

### Worker Features ✅
- [ ] See "CREATE NEW SUBMISSION" button on task page
- [ ] Click to create a new draft submission
- [ ] See "CONTINUE EDITING DRAFT" button after creating draft
- [ ] Click to edit the draft
- [ ] See "SAVE CHANGES" button on submission form
- [ ] See "SUBMIT FOR REVIEW" button on submission detail
- [ ] Click to submit draft for manager review
- [ ] See submission status timeline showing progress

### Manager Features ✅
- [ ] See "MANAGER REVIEW" panel immediately after worker submits
- [ ] Panel appears when status = "submitted" (not just "under_review")
- [ ] Add feedback text (optional)
- [ ] Enter score 0-100 (optional)
- [ ] Click "APPROVE SUBMISSION" button
- [ ] Click "REJECT SUBMISSION" button
- [ ] See status change to "approved" or "rejected"
- [ ] See review details preserved (feedback & score)

---

## Files That Were Fixed

1. `templates/pages/task_detail.html`
   - Line 172: Worker panel visibility condition
   - Lines 180-195: Button state logic

2. `templates/pages/submission_detail.html`
   - Line 125: Manager review panel visibility
   - Lines 128-160: Review button implementation

**All other files remain unchanged** - This was a pure template-logic fix with no backend changes needed.

---

**Last Updated**: February 24, 2026  
**Status**: ✅ Ready for Testing  
**Support**: If issues persist, check BUTTON_FIXES_VERIFICATION.md or GUI_FIXES_SUMMARY.md
