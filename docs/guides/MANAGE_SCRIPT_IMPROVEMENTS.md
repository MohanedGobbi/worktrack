# Manage.sh Script Improvements - WorkTrack Pro GUI Edition

## Overview
The `manage.sh` script has been redesigned to **support the new GUI web application** with Bootstrap 5 UI and includes the requested **"stop all running servers"** feature.

---

## 🎯 Key Improvements

### 1. **New "Stop All Servers" Feature** ⭐
   - **Command:** `./manage.sh stopall`
   - **Function:** `stop_all_servers()`
   - **Capabilities:**
     - Finds ALL Django processes running `python manage.py runserver`
     - Displays list of found processes with PIDs
     - Asks for confirmation before terminating
     - Gracefully terminates processes with SIGTERM
     - Force kills remaining processes with SIGKILL
     - Cleans up PID files
   - **Use Case:** Quick cleanup when multiple server instances are running

### 2. **GUI-Focused Application URLs**
   - Updated all access point displays from API-only (`/api`) to full GUI system
   - **New URLs shown:**
     - 🌐 Home Page: `http://localhost:8000`
     - 🏠 Dashboard: `http://localhost:8000/dashboard`
     - ✅ Tasks: `http://localhost:8000/tasks`
     - 📥 Submissions: `http://localhost:8000/submissions`
     - 🔔 Notifications: `http://localhost:8000/notifications`
     - 👤 Profile: `http://localhost:8000/profile`
     - ⚙️ Admin Panel: `http://localhost:8000/admin`
     - 📊 API Endpoints: `http://localhost:8000/api`

### 3. **New "Test Accounts" Command**
   - **Command:** `./manage.sh accounts`
   - **Function:** `show_test_accounts()`
   - **Displays:**
     - Admin account with full system access
     - Manager account for task/submission review
     - Two worker accounts (Alice Smith & Bob Jones)
     - Email and password credentials
   - **Use Case:** Quick reference for testing without searching documentation

### 4. **New "Server Logs" Command**
   - **Command:** `./manage.sh logs`
   - **Function:** `tail_logs()`
   - **Features:**
     - Real-time server log streaming
     - Uses dedicated log file in `logs/server.log`
     - Exit with Ctrl+C
   - **Use Case:** Monitor server activity and debug issues in real-time

### 5. **Improved Help Documentation**
   - **Command:** `./manage.sh help` (or `--help` or `-h`)
   - **Displays:**
     - Project name and type (GUI Edition)
     - All available commands grouped by category
     - Usage examples
     - Complete list of application URLs
   - **Better Organization:**
     - Setup Commands (3)
     - Database Commands (4)
     - Server Commands (6)
     - Utilities (4)

### 6. **Enhanced Interactive Menu**
   - **Command:** `./manage.sh menu` or `./manage.sh` (default)
   - **New Structure (16 options):**
     - 📦 Setup & Installation (3 options)
     - 💾 Database Management (4 options)
     - 🚀 Server Management (6 options) - NOW INCLUDES "Stop All Servers"
     - 🔧 Utilities (3 options) - NOW INCLUDES "Test Accounts"
   - **Better Positioning:**
     - "Stop All Servers" option: #10
     - "Test Accounts" option: #15
     - "View Server Logs" option: #13

### 7. **Enhanced Server Start Output**
   - Shows all 8 access points when server starts
   - Prettier formatting with icons
   - Log file path information
   - Quick reference for stopping the server

### 8. **Improved Server Status Display**
   - Shows whether server is RUNNING or NOT RUNNING
   - Displays PID when running
   - Shows all 8 application access points
   - Better visual separation with dividers

### 9. **Better Code Organization**
   - Helper functions for printing common elements
   - `print_divider()` for visual separation
   - Consistent formatting throughout
   - Improved comments and documentation

### 10. **Dedicated Log Directory**
   - Create dedicated `logs/` directory
   - Server logs are stored in `logs/server.log`
   - Persistent logs across multiple server restarts
   - Better than temporary files for production

---

## 📋 Complete Command Reference

### Setup Commands
```bash
./manage.sh setup              # Full application setup
./manage.sh venv               # Create/recreate virtual environment
./manage.sh install            # Install dependencies from requirements.txt
```

### Database Commands
```bash
./manage.sh makemig            # Create migrations (interactive)
./manage.sh migrate            # Apply pending migrations
./manage.sh static             # Collect static files
./manage.sh superuser          # Create admin account
```

### Server Commands
```bash
./manage.sh start              # Start development server on port 8000
./manage.sh stop               # Stop the running server
./manage.sh stopall            # Stop ALL running Django servers
./manage.sh status             # Check if server is running
./manage.sh restart            # Restart the server
./manage.sh logs               # View real-time server logs
```

### Utilities
```bash
./manage.sh shell              # Open Django interactive shell
./manage.sh dbinfo             # Show database information
./manage.sh accounts           # Display test account credentials
./manage.sh menu               # Interactive menu (default)
./manage.sh help               # Show help documentation
```

---

## 🚀 New Workflow Examples

### Example 1: Testing Multiple Server Instances
```bash
# Terminal 1: Start server
./manage.sh start

# Terminal 2: Start another server (will warn about existing)
./manage.sh start

# Clean up all servers at once
./manage.sh stopall
```

### Example 2: Quick Application Access
```bash
# Show all access points
./manage.sh status

# Get test credentials
./manage.sh accounts

# Monitor server logs
./manage.sh logs
```

### Example 3: Fresh Setup
```bash
./manage.sh setup              # Complete setup
./manage.sh accounts           # Check test credentials
./manage.sh start              # Start application
# Browse to http://localhost:8000
```

---

## 📊 Comparison: Before vs After

| Feature | Before | After |
|---------|--------|-------|
| Stop All Servers | ❌ No | ✅ Yes (`stopall`) |
| Test Accounts Command | ❌ No | ✅ Yes (`accounts`) |
| Server Logs Command | ❌ No | ✅ Yes (`logs`) |
| GUI URLs in Status | ❌ Only API | ✅ All 8 access points |
| Help Command | ❌ Limited | ✅ Comprehensive |
| Menu Options | 13 | **16** |
| Server Processes | Single (PID) | All (pgrep) |
| Log File | Temporary | Persistent (`logs/server.log`) |
| Code Organization | Basic | **Enhanced with helpers** |

---

## 🔧 Technical Details

### Stop All Servers Implementation
The `stop_all_servers()` function:
1. Uses `pgrep -f "python.*manage.py runserver"` to find all Django processes
2. Displays each process with its PID and command line
3. Requests user confirmation
4. Terminates with SIGTERM (graceful)
5. Waits 1 second, then force kills with SIGKILL if needed
6. Cleans up `.server.pid` file

### Test Accounts Display
The `show_test_accounts()` function displays:
- **admin@worktrack.local** - Super Admin role
- **manager@worktrack.local** - Manager role
- **worker1@worktrack.local** - Alice Smith (Worker)
- **worker2@worktrack.local** - Bob Jones (Worker)

All with password: `***@123456` (see actual script for full passwords)

### Server Logging
- Logs stored in: `$PROJECT_DIR/logs/server.log`
- Created automatically on server start
- Viewable with: `./manage.sh logs`
- Persistent across restarts

---

## ✨ Additional Features

### Color-Coded Output
- ✅ Green for success
- ❌ Red for errors
- ⚠️ Yellow for warnings
- ℹ️ Blue for info

### Better Formatting
- Unicode box drawing characters for headers
- Emoji icons for easy scanning
- Consistent spacing and indentation
- Visual separators between sections

### Error Handling
- Checks for virtual environment before activation
- Validates required files and directories
- Graceful error messages
- PID file cleanup on failures

---

## 🎯 Use Cases

1. **Development:** Use `./manage.sh start` and `./manage.sh logs` for local development
2. **Testing:** Use `./manage.sh accounts` and `./manage.sh status` for testing
3. **Cleanup:** Use `./manage.sh stopall` when multiple servers are running
4. **Production:** Use `./manage.sh setup` for fresh deployment
5. **Learning:** Use `./manage.sh menu` for interactive guided workflow

---

## 📝 Summary

The redesigned manage.sh script now:
- ✅ Supports the **new GUI web application** with proper access points
- ✅ Includes **"stop all servers"** feature for multi-instance cleanup
- ✅ Displays **test account credentials** for easy reference
- ✅ Provides **server logging** with real-time monitoring
- ✅ Has **improved help** and documentation
- ✅ Offers **better interactive menu** with more options
- ✅ Uses **dedicated logs directory** for production readiness
- ✅ Maintains **backward compatibility** with existing commands

All while keeping the script simple, readable, and maintainable!
