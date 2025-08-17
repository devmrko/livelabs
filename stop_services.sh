#!/bin/bash
#
# LiveLabs REST API Services Shutdown Script
# Stops all running REST API services using saved PIDs
#

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIDS_DIR="$SCRIPT_DIR/pids"

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

print_header "🛑 Stopping LiveLabs REST API Services"

# Check if PIDs directory exists
if [ ! -d "$PIDS_DIR" ]; then
    print_error "PIDs directory not found: $PIDS_DIR"
    print_status "No services to stop or services were not started with start_services.sh"
    exit 1
fi

# Service definitions (must match start_services.sh)
SERVICES_semantic_search="8001"
SERVICES_nl_query="8002"
SERVICES_user_skills_progression="8003"

# Service names array
SERVICE_NAMES=("semantic_search" "nl_query" "user_skills_progression")

# Function to stop a service
stop_service() {
    local service_name=$1
    local port=$2
    local pid_file="$PIDS_DIR/${service_name}.pid"
    
    print_status "Stopping $service_name service..."
    
    if [ ! -f "$pid_file" ]; then
        print_warning "PID file not found: $pid_file"
        
        # Try to find process by port
        local port_pid=$(lsof -Pi :$port -sTCP:LISTEN -t 2>/dev/null)
        if [ -n "$port_pid" ]; then
            print_warning "Found process on port $port (PID: $port_pid), attempting to stop..."
            if kill -TERM $port_pid 2>/dev/null; then
                sleep 2
                if kill -0 $port_pid 2>/dev/null; then
                    print_warning "Process still running, using SIGKILL..."
                    kill -KILL $port_pid 2>/dev/null
                fi
                print_status "✅ Stopped process on port $port"
            else
                print_error "❌ Failed to stop process on port $port"
                return 1
            fi
        else
            print_status "No process found on port $port"
        fi
        return 0
    fi
    
    local pid=$(cat "$pid_file")
    print_status "Found PID: $pid"
    
    # Check if process is still running
    if ! kill -0 $pid 2>/dev/null; then
        print_warning "Process $pid is not running"
        rm -f "$pid_file"
        return 0
    fi
    
    # Try graceful shutdown first
    print_status "Sending SIGTERM to PID $pid..."
    if kill -TERM $pid 2>/dev/null; then
        # Wait up to 10 seconds for graceful shutdown
        local count=0
        while [ $count -lt 10 ] && kill -0 $pid 2>/dev/null; do
            sleep 1
            ((count++))
        done
        
        # Check if process stopped
        if kill -0 $pid 2>/dev/null; then
            print_warning "Process still running after SIGTERM, using SIGKILL..."
            kill -KILL $pid 2>/dev/null
            sleep 1
        fi
        
        # Final check
        if kill -0 $pid 2>/dev/null; then
            print_error "❌ Failed to stop $service_name (PID: $pid)"
            return 1
        else
            print_status "✅ $service_name stopped successfully"
            rm -f "$pid_file"
            return 0
        fi
    else
        print_error "❌ Failed to send signal to PID $pid"
        return 1
    fi
}

# Stop all services
print_header "Stopping services..."
stopped_services=()
failed_services=()

for service_name in "${SERVICE_NAMES[@]}"; do
    echo
    # Get port using variable indirection
    service_var="SERVICES_${service_name}"
    port="${!service_var}"
    if stop_service "$service_name" "$port"; then
        stopped_services+=("$service_name")
    else
        failed_services+=("$service_name")
    fi
done

# Summary
echo
print_header "🎯 Shutdown Summary"
if [ ${#failed_services[@]} -eq 0 ]; then
    print_status "✅ All services stopped successfully!"
    if [ ${#stopped_services[@]} -gt 0 ]; then
        print_status "📊 Stopped services:"
        for service in "${stopped_services[@]}"; do
            print_status "  • $service"
        done
    fi
    
    # Clean up empty PID files
    find "$PIDS_DIR" -name "*.pid" -empty -delete 2>/dev/null
    
    print_status "🧹 Cleanup completed"
else
    print_error "❌ Some services failed to stop:"
    for service in "${failed_services[@]}"; do
        print_error "  • $service"
    done
    
    print_status "💡 You may need to manually kill remaining processes:"
    print_status "   ps aux | grep 'rest_livelabs'"
    print_status "   kill -9 <PID>"
    exit 1
fi
