#!/bin/bash

# WorkTrack Pro - Simple Interactive Menu
# Delegates all server management to manage.sh
# SQLite database, local Django server only

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ANSI Colors
RED=$'\033[0;31m'
GREEN=$'\033[0;32m'
YELLOW=$'\033[1;33m'
CYAN=$'\033[0;36m'
BOLD=$'\033[1m'
NC=$'\033[0m'

print_banner() {
    clear
    cat << "EOF"
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║                     ✨ WorkTrack Pro - Manager ✨                          ║
║                                                                            ║
║                  Workforce Management System - v1.0.0                      ║
║                   SQLite Database | Local Django Server                    ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
EOF
    echo ""
}

show_menu() {
    print_banner
    cat << "EOF"
  📋 Quick Actions:
  
    $(printf '%b' "${CYAN}1${NC}") - Full Setup (venv, deps, db, admin)
    $(printf '%b' "${CYAN}2${NC}") - Start Django Server
    $(printf '%b' "${CYAN}3${NC}") - Stop Server
    $(printf '%b' "${CYAN}4${NC}") - Server Status
    $(printf '%b' "${CYAN}5${NC}") - Restart Server
    
  🔧 Database & Apps:
  
    $(printf '%b' "${CYAN}6${NC}") - Make Migrations
    $(printf '%b' "${CYAN}7${NC}") - Run Migrations
    $(printf '%b' "${CYAN}8${NC}") - Collect Static Files
    $(printf '%b' "${CYAN}9${NC}") - Create Superuser
    $(printf '%b' "${CYAN}10${NC}") - Django Shell
    
  ℹ️  Info:
  
    $(printf '%b' "${CYAN}11${NC}") - Database Info
    $(printf '%b' "${CYAN}12${NC}") - Full Menu (manage.sh)
    
    $(printf '%b' "${CYAN}0${NC}") - Exit

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF
}

main_menu() {
    while true; do
        show_menu
        read -p "Select option: " choice

        case $choice in
            1) "$PROJECT_DIR/manage_v6.sh" setup ;;
            2) "$PROJECT_DIR/manage_v6.sh" start ;;
            3) "$PROJECT_DIR/manage_v6.sh" stop ;;
            4) "$PROJECT_DIR/manage_v6.sh" status ;;
            5) "$PROJECT_DIR/manage_v6.sh" restart ;;
            6) "$PROJECT_DIR/manage_v6.sh" makemig ;;
            7) "$PROJECT_DIR/manage_v6.sh" migrate ;;
            8) "$PROJECT_DIR/manage_v6.sh" static ;;
            9) "$PROJECT_DIR/manage_v6.sh" superuser ;;
            10) "$PROJECT_DIR/manage_v6.sh" shell ;;
            11) "$PROJECT_DIR/manage_v6.sh" dbinfo ;;
            12) "$PROJECT_DIR/manage_v6.sh" menu ;;
            0)
                clear
                printf '%b\n' "${GREEN}✓ Goodbye!${NC}"
                echo ""
                exit 0
                ;;
            *)
                printf '%b\n' "${RED}✗ Invalid option${NC}"
                read -p "Press Enter to continue..." ;;
        esac
    done
}

main_menu
