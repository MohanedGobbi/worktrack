#!/bin/bash

# WorkTrack Pro - Server Control Script
# Usage: ./server.sh [start|stop|restart|status|docker-start|docker-stop]

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"
PID_FILE="$PROJECT_DIR/.server.pid"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "${BLUE}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Activate virtual environment
activate_venv() {
    local venv_broken=false
    if [ -d "$VENV_DIR" ]; then
        if [ ! -f "$VENV_DIR/bin/python" ] || ! "$VENV_DIR/bin/python" -c "import sys" &>/dev/null; then
            venv_broken=true
        else
            local venv_path=""
            if [ -f "$VENV_DIR/bin/activate" ]; then
                venv_path=$(grep -E "^export VIRTUAL_ENV=" "$VENV_DIR/bin/activate" 2>/dev/null | head -n1 | sed -E 's/.*=["'\''"]?(.*)["'\''"]?/\1/' | tr -d '"' | tr -d "'")
            fi
            if [ -n "$venv_path" ] && [ "$venv_path" != "$VENV_DIR" ]; then
                venv_broken=true
            fi
        fi

        if [ "$venv_broken" = true ]; then
            print_warning "Detecting moved or broken virtual environment!"
            print_header "Auto-repairing virtual environment (.venv)..."
            rm -rf "$VENV_DIR"
            python3 -m venv "$VENV_DIR"
            "$VENV_DIR/bin/pip" install --upgrade pip -q 2>/dev/null || true
            if [ -f "$PROJECT_DIR/requirements.txt" ]; then
                "$VENV_DIR/bin/pip" install -r "$PROJECT_DIR/requirements.txt" -q 2>/dev/null || "$VENV_DIR/bin/pip" install -r "$PROJECT_DIR/requirements.txt"
            fi
            print_success "Virtual environment auto-repaired!"
        fi
        source "$VENV_DIR/bin/activate"
        print_success "Virtual environment activated"
    else
        print_header "Creating virtual environment at $VENV_DIR ..."
        python3 -m venv "$VENV_DIR"
        "$VENV_DIR/bin/pip" install --upgrade pip -q 2>/dev/null || true
        if [ -f "$PROJECT_DIR/requirements.txt" ]; then
            "$VENV_DIR/bin/pip" install -r "$PROJECT_DIR/requirements.txt" -q 2>/dev/null || "$VENV_DIR/bin/pip" install -r "$PROJECT_DIR/requirements.txt"
        fi
        source "$VENV_DIR/bin/activate"
        print_success "Virtual environment initialized and activated"
    fi
}

# Start local development server
start_local() {
    print_header "Starting Django development server..."
    
    cd "$PROJECT_DIR"
    activate_venv
    
    # Check if server is already running
    if [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE")
        if kill -0 "$OLD_PID" 2>/dev/null; then
            print_warning "Server already running with PID $OLD_PID"
            return 1
        fi
    fi
    
    # Start server
    python manage.py runserver 0.0.0.0:8000 > /tmp/django_server.log 2>&1 &
    SERVER_PID=$!
    echo $SERVER_PID > "$PID_FILE"
    
    sleep 2
    
    # Check if server started successfully
    if kill -0 "$SERVER_PID" 2>/dev/null; then
        print_success "Django server started with PID $SERVER_PID"
        echo ""
        echo "Access points:"
        echo "  API:      http://localhost:8000/api"
        echo "  Admin:    http://localhost:8000/admin"
        echo "  Schema:   http://localhost:8000/api/schema/"
        echo ""
        print_warning "Press Ctrl+C to stop the server"
        wait $SERVER_PID
    else
        print_error "Failed to start server. Check /tmp/django_server.log"
        cat /tmp/django_server.log
        exit 1
    fi
}

# Stop local development server
stop_local() {
    print_header "Stopping Django development server..."
    
    if [ ! -f "$PID_FILE" ]; then
        print_warning "No PID file found. Server may not be running."
        # Try to kill by port
        pkill -f "runserver" || true
        return 0
    fi
    
    PID=$(cat "$PID_FILE")
    
    if kill -0 "$PID" 2>/dev/null; then
        kill $PID
        sleep 1
        
        if kill -0 "$PID" 2>/dev/null; then
            print_warning "Process still running, forcing kill..."
            kill -9 $PID
            sleep 1
        fi
        
        rm -f "$PID_FILE"
        print_success "Server stopped (PID $PID)"
    else
        print_warning "Process not running (PID $PID)"
        rm -f "$PID_FILE"
    fi
}

# Restart local development server
restart_local() {
    print_header "Restarting Django development server..."
    stop_local
    sleep 2
    start_local
}

# Check server status
status_local() {
    print_header "Checking server status..."
    
    if [ ! -f "$PID_FILE" ]; then
        print_warning "Server appears to be stopped (no PID file)"
        return 1
    fi
    
    PID=$(cat "$PID_FILE")
    
    if kill -0 "$PID" 2>/dev/null; then
        print_success "Server is running (PID: $PID)"
        
        # Try to get more info
        if command -v lsof &> /dev/null; then
            echo ""
            echo "Port information:"
            lsof -i :8000 || echo "  No process found on port 8000"
        fi
        
        return 0
    else
        print_error "Server not running (stale PID: $PID)"
        rm -f "$PID_FILE"
        return 1
    fi
}

# Start Docker stack
start_docker() {
    print_header "Starting WorkTrack Pro with Docker..."
    
    cd "$PROJECT_DIR"
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "docker-compose not found. Please install Docker Desktop."
        exit 1
    fi
    
    docker-compose up -d
    
    sleep 3
    
    print_success "Docker services started"
    echo ""
    echo "Services:"
    echo "  API:         http://localhost:8000/api"
    echo "  Admin:       http://localhost:8000/admin"
    echo "  PostgreSQL:  localhost:5432"
    echo "  Redis:       localhost:6379"
    echo ""
    echo "View logs: docker-compose logs -f web"
}

# Stop Docker stack
stop_docker() {
    print_header "Stopping WorkTrack Pro Docker services..."
    
    cd "$PROJECT_DIR"
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "docker-compose not found"
        exit 1
    fi
    
    docker-compose down
    print_success "Docker services stopped"
}

# Restart Docker stack
restart_docker() {
    print_header "Restarting WorkTrack Pro Docker services..."
    stop_docker
    sleep 2
    start_docker
}

# Status of Docker services
status_docker() {
    print_header "Checking Docker services status..."
    
    cd "$PROJECT_DIR"
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "docker-compose not found"
        exit 1
    fi
    
    docker-compose ps
}

# Show logs
show_logs() {
    print_header "Showing server logs..."
    
    MODE=${1:-local}
    
    if [ "$MODE" = "docker" ]; then
        cd "$PROJECT_DIR"
        docker-compose logs -f web
    else
        if [ -f "/tmp/django_server.log" ]; then
            tail -f /tmp/django_server.log
        else
            print_warning "No log file found"
        fi
    fi
}

# Show help
show_help() {
    cat << EOF
${BLUE}WorkTrack Pro - Server Control Script${NC}

${BLUE}USAGE:${NC}
  ./server.sh [COMMAND] [OPTIONS]

${BLUE}COMMANDS:${NC}
  Local Development:
    start                 Start Django dev server
    stop                  Stop Django dev server
    restart               Restart Django dev server
    status                Check server status
    logs                  View server logs

  Docker:
    docker-start          Start Docker stack (PostgreSQL, Redis, Django, Celery)
    docker-stop           Stop Docker stack
    docker-restart        Restart Docker stack
    docker-status         Check Docker services status
    docker-logs           View Docker logs

  General:
    help                  Show this help message

${BLUE}EXAMPLES:${NC}
  ./server.sh start               # Start local dev server
  ./server.sh docker-start        # Start with Docker
  ./server.sh restart             # Restart local server
  ./server.sh status              # Check if server is running
  ./server.sh logs                # View logs
  ./server.sh docker-logs         # View Docker logs

${BLUE}REQUIREMENTS:${NC}
  Local: Python 3.8+, Virtual environment with dependencies
  Docker: Docker and Docker Compose installed

${BLUE}ACCESS POINTS:${NC}
  API:      http://localhost:8000/api
  Admin:    http://localhost:8000/admin
  Docs:     http://localhost:8000/api/docs/ (if DRF spectacular installed)

EOF
}

# Main command handler
main() {
    COMMAND=${1:-help}
    
    case "$COMMAND" in
        start)
            start_local
            ;;
        stop)
            stop_local
            ;;
        restart)
            restart_local
            ;;
        status)
            status_local
            ;;
        logs)
            show_logs local
            ;;
        docker-start)
            start_docker
            ;;
        docker-stop)
            stop_docker
            ;;
        docker-restart)
            restart_docker
            ;;
        docker-status)
            status_docker
            ;;
        docker-logs)
            show_logs docker
            ;;
        help|-h|--help)
            show_help
            ;;
        *)
            print_error "Unknown command: $COMMAND"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
