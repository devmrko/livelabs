#!/bin/bash
#
# LiveLabs REST API Services Startup Script
# Starts all REST API services in detached mode with PID tracking and logging
#

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MCP_DIR="$SCRIPT_DIR/MCP"
LOGS_DIR="$SCRIPT_DIR/logs"
PIDS_DIR="$SCRIPT_DIR/pids"
VENV_DIR="$SCRIPT_DIR/venv"
PYTHON_BIN="$VENV_DIR/bin/python"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[HEADER]${NC} $1"
}

# Create necessary directories
mkdir -p "$LOGS_DIR" "$PIDS_DIR"

print_header "🚀 Starting LiveLabs REST API Services"
print_status "Logs directory: $LOGS_DIR"
print_status "PIDs directory: $PIDS_DIR"
print_status "Python binary: $PYTHON_BIN"
print_status "Timestamp: $TIMESTAMP"

# Check if virtual environment exists
if [ ! -f "$PYTHON_BIN" ]; then
    print_error "Virtual environment not found at: $VENV_DIR"
    print_error "Please create virtual environment first: python -m venv venv"
    exit 1
fi

# Service definitions (compatible with older bash)
SERVICES_semantic_search="rest_livelabs_semantic_search.py:8001"
SERVICES_nl_query="rest_livelabs_nl_query.py:8002"
SERVICES_user_skills_progression="rest_livelabs_user_skills_progression.py:8003"

# Service names array
SERVICE_NAMES=("semantic_search" "nl_query" "user_skills_progression")

# Function to start a service
start_service() {
    local service_name=$1
    local service_info=$2
    local script_name=$(echo $service_info | cut -d':' -f1)
    local port=$(echo $service_info | cut -d':' -f2)
    
    local script_path="$MCP_DIR/$script_name"
    local log_file="$LOGS_DIR/${service_name}_${TIMESTAMP}.log"
    local pid_file="$PIDS_DIR/${service_name}.pid"
    
    print_status "Starting $service_name service..."
    print_status "  Script: $script_path"
    print_status "  Port: $port"
    print_status "  Log: $log_file"
    print_status "  PID file: $pid_file"
    
    # Check if script exists
    if [ ! -f "$script_path" ]; then
        print_error "Script not found: $script_path"
        return 1
    fi
    
    # Check if port is already in use
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_warning "Port $port is already in use. Checking if it's our service..."
        local existing_pid=$(lsof -Pi :$port -sTCP:LISTEN -t)
        if [ -f "$pid_file" ] && [ "$(cat $pid_file 2>/dev/null)" = "$existing_pid" ]; then
            print_warning "$service_name is already running with PID $existing_pid"
            return 0
        else
            print_error "Port $port is occupied by another process (PID: $existing_pid)"
            return 1
        fi
    fi
    
    # Start the service in background using virtual environment
    cd "$SCRIPT_DIR"
    nohup "$PYTHON_BIN" "$script_path" > "$log_file" 2>&1 &
    local service_pid=$!
    
    # Save PID
    echo $service_pid > "$pid_file"
    
    # Wait a moment and check if service started successfully
    sleep 2
    if kill -0 $service_pid 2>/dev/null; then
        print_status "✅ $service_name started successfully (PID: $service_pid)"
        
        # Wait for service to be ready (check port)
        local max_attempts=10
        local attempt=1
        while [ $attempt -le $max_attempts ]; do
            if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
                print_status "✅ $service_name is ready on port $port"
                break
            fi
            print_status "Waiting for $service_name to be ready... ($attempt/$max_attempts)"
            sleep 1
            ((attempt++))
        done
        
        if [ $attempt -gt $max_attempts ]; then
            print_warning "⚠️  $service_name may not be fully ready yet"
        fi
    else
        print_error "❌ Failed to start $service_name"
        rm -f "$pid_file"
        return 1
    fi
}

# Start all services
print_header "Starting services..."
failed_services=()

for service_name in "${SERVICE_NAMES[@]}"; do
    echo
    # Get service info using variable indirection
    service_var="SERVICES_${service_name}"
    service_info="${!service_var}"
    if ! start_service "$service_name" "$service_info"; then
        failed_services+=("$service_name")
    fi
done

# Summary
echo
print_header "🎯 Startup Summary"
if [ ${#failed_services[@]} -eq 0 ]; then
    print_status "✅ All services started successfully!"
    print_status "📊 Service Status:"
    for service_name in "${SERVICE_NAMES[@]}"; do
        service_var="SERVICES_${service_name}"
        service_info="${!service_var}"
        port=$(echo "$service_info" | cut -d':' -f2)
        pid_file="$PIDS_DIR/${service_name}.pid"
        if [ -f "$pid_file" ]; then
            pid=$(cat "$pid_file")
            print_status "  • $service_name: PID $pid, Port $port"
        fi
    done
    
    echo
    print_status "📝 Log files location: $LOGS_DIR"
    print_status "🔧 PID files location: $PIDS_DIR"
    print_status "🛑 To stop services: ./stop_services.sh"
    
else
    print_error "❌ Some services failed to start:"
    for service in "${failed_services[@]}"; do
        print_error "  • $service"
    done
    exit 1
fi
