#!/bin/bash

# DragonFruit Grading - Setup Script
# This script helps you set up the complete integration

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
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

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Main script
main() {
    print_header "DragonFruit Grading - Integration Setup"
    
    echo "This script will help you set up the Camera → Backend → Database integration."
    echo ""
    echo "Prerequisites:"
    echo "  • Python 3.8+"
    echo "  • PostgreSQL running"
    echo "  • pip (Python package manager)"
    echo ""
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 not found. Please install Python 3.8 or higher."
        exit 1
    fi
    print_success "Python found: $(python3 --version)"
    
    # Check PostgreSQL
    if ! command -v psql &> /dev/null; then
        print_warning "PostgreSQL client not found. Make sure PostgreSQL server is running."
    else
        print_success "PostgreSQL found: $(psql --version)"
    fi
    
    # Step 1: Backend setup
    print_header "Step 1: Backend Setup"
    
    if [ ! -d "backend" ]; then
        print_error "backend directory not found. Make sure you're in the project root."
        exit 1
    fi
    
    cd backend
    
    # Install dependencies
    print_info "Installing Python dependencies..."
    pip install -r requirements.txt > /dev/null 2>&1 || {
        print_error "Failed to install dependencies"
        exit 1
    }
    print_success "Dependencies installed"
    
    # Create .env if not exists
    if [ ! -f ".env" ]; then
        print_info "Creating .env file..."
        cat > .env << EOF
# Database Configuration
DB_USER=postgres
DB_PASS=postgres
DB_HOST=localhost
DB_PORT=5432
DB_NAME=dragonfruit

# MQTT Configuration
MQTT_BROKER=localhost
MQTT_PORT=1883

# API Configuration
ENV=development
DEBUG=True
EOF
        print_success ".env file created"
        print_warning "Please update .env with your database credentials"
    else
        print_success ".env file already exists"
    fi
    
    cd ..
    
    # Step 2: Camera setup
    print_header "Step 2: Camera Setup"
    
    if [ ! -f "iot/camera.py" ]; then
        print_error "camera.py not found"
        exit 1
    fi
    
    print_info "Installing camera dependencies..."
    pip install requests opencv-python > /dev/null 2>&1 || {
        print_error "Failed to install camera dependencies"
        exit 1
    }
    print_success "Camera dependencies installed"
    
    # Step 3: Verify database
    print_header "Step 3: Database Verification"
    
    print_info "Checking PostgreSQL connection..."
    
    if psql -U postgres -c "SELECT 1" > /dev/null 2>&1; then
        print_success "PostgreSQL is running"
        
        # Create database if not exists
        psql -U postgres -c "CREATE DATABASE dragonfruit;" 2>/dev/null || print_success "Database already exists"
        print_success "Database ready"
    else
        print_warning "Could not connect to PostgreSQL"
        print_info "Make sure PostgreSQL is running with user 'postgres'"
    fi
    
    # Step 4: Installation summary
    print_header "Installation Complete! ✨"
    
    echo "Next steps:"
    echo ""
    echo "1. Start the backend server:"
    echo "   ${BLUE}cd backend && python main.py${NC}"
    echo ""
    echo "2. Create database tables (in another terminal):"
    echo "   ${BLUE}curl -X POST http://localhost:8000/debug/create-tables${NC}"
    echo ""
    echo "3. Update camera.py if needed (line 34):"
    echo "   ${BLUE}BACKEND_URL = \"http://localhost:8000/api\"${NC}"
    echo ""
    echo "4. Start the camera:"
    echo "   ${BLUE}python iot/camera.py${NC}"
    echo ""
    echo "5. Run tests:"
    echo "   ${BLUE}python test_insertdata_client.py${NC}"
    echo ""
    echo "6. Press 's' in camera window to capture and send to database"
    echo ""
    echo "For more information, see:"
    echo "  • INTEGRATION_GUIDE.md - Complete setup guide"
    echo "  • QUICK_REFERENCE.md - Quick lookup"
    echo "  • ARCHITECTURE_DIAGRAMS.md - System architecture"
    echo ""
    print_success "Setup complete!"
}

# Run main
main
