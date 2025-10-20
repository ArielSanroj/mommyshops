#!/bin/bash

# MommyShops Production Environment Setup Script
# Based on start.py and api_utils_production.py functionality

set -e

echo "🔧 Setting up MommyShops Production Environment"
echo "==============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install package
install_package() {
    local package=$1
    local install_cmd=$2
    
    if ! command_exists $package; then
        print_status $BLUE "Installing $package..."
        eval $install_cmd
        print_status $GREEN "✅ $package installed"
    else
        print_status $GREEN "✅ $package already installed"
    fi
}

# Check if running on macOS or Linux
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
else
    print_status $RED "❌ Unsupported operating system: $OSTYPE"
    exit 1
fi

print_status $BLUE "🖥️  Detected operating system: $OS"

# Install Java 21
print_status $BLUE "☕ Installing Java 21..."

if [ "$OS" = "macos" ]; then
    if command_exists brew; then
        install_package "java" "brew install openjdk@21"
        # Set JAVA_HOME
        export JAVA_HOME=$(/usr/libexec/java_home -v 21)
        echo 'export JAVA_HOME=$(/usr/libexec/java_home -v 21)' >> ~/.zshrc
    else
        print_status $RED "❌ Homebrew not found. Please install Homebrew first."
        exit 1
    fi
elif [ "$OS" = "linux" ]; then
    # Update package list
    sudo apt-get update
    
    # Install Java 21
    install_package "java" "sudo apt-get install -y openjdk-21-jdk"
    
    # Set JAVA_HOME
    export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
    echo 'export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64' >> ~/.bashrc
fi

# Verify Java installation
if command_exists java; then
    JAVA_VERSION=$(java -version 2>&1 | head -n 1 | cut -d'"' -f2 | cut -d'.' -f1)
    if [ "$JAVA_VERSION" -ge 21 ]; then
        print_status $GREEN "✅ Java $JAVA_VERSION is installed"
    else
        print_status $RED "❌ Java version $JAVA_VERSION is not supported. Please install Java 21 or higher."
        exit 1
    fi
else
    print_status $RED "❌ Java installation failed"
    exit 1
fi

# Install Maven
print_status $BLUE "🔨 Installing Maven..."

if [ "$OS" = "macos" ]; then
    install_package "mvn" "brew install maven"
elif [ "$OS" = "linux" ]; then
    install_package "mvn" "sudo apt-get install -y maven"
fi

# Verify Maven installation
if command_exists mvn; then
    MVN_VERSION=$(mvn -version | head -n 1 | cut -d' ' -f3)
    print_status $GREEN "✅ Maven $MVN_VERSION is installed"
else
    print_status $RED "❌ Maven installation failed"
    exit 1
fi

# Install Docker
print_status $BLUE "🐳 Installing Docker..."

if [ "$OS" = "macos" ]; then
    if ! command_exists docker; then
        print_status $BLUE "Please install Docker Desktop for Mac from https://www.docker.com/products/docker-desktop"
        print_status $YELLOW "After installation, please run this script again."
        exit 1
    fi
elif [ "$OS" = "linux" ]; then
    install_package "docker" "sudo apt-get install -y docker.io docker-compose"
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker $USER
fi

# Verify Docker installation
if command_exists docker; then
    DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
    print_status $GREEN "✅ Docker $DOCKER_VERSION is installed"
else
    print_status $RED "❌ Docker installation failed"
    exit 1
fi

# Install Ollama
print_status $BLUE "🤖 Installing Ollama..."

if [ "$OS" = "macos" ]; then
    if ! command_exists ollama; then
        print_status $BLUE "Installing Ollama for macOS..."
        curl -fsSL https://ollama.ai/install.sh | sh
    fi
elif [ "$OS" = "linux" ]; then
    if ! command_exists ollama; then
        print_status $BLUE "Installing Ollama for Linux..."
        curl -fsSL https://ollama.ai/install.sh | sh
    fi
fi

# Verify Ollama installation
if command_exists ollama; then
    OLLAMA_VERSION=$(ollama --version | cut -d' ' -f2)
    print_status $GREEN "✅ Ollama $OLLAMA_VERSION is installed"
else
    print_status $RED "❌ Ollama installation failed"
    exit 1
fi

# Start Ollama service
print_status $BLUE "🚀 Starting Ollama service..."
ollama serve &
sleep 5

# Verify Ollama is running
if curl -s http://localhost:11434/api/version >/dev/null 2>&1; then
    print_status $GREEN "✅ Ollama service is running"
else
    print_status $RED "❌ Ollama service failed to start"
    exit 1
fi

# Pull required Ollama models
print_status $BLUE "📥 Pulling required Ollama models..."

# Pull llama3.1 model
print_status $BLUE "Pulling llama3.1 model..."
ollama pull llama3.1

# Pull llava model
print_status $BLUE "Pulling llava model..."
ollama pull llava

print_status $GREEN "✅ Required Ollama models are available"

# Create necessary directories
print_status $BLUE "📁 Creating necessary directories..."
mkdir -p logs
mkdir -p data
mkdir -p config

print_status $GREEN "✅ Directories created"

# Create environment file
print_status $BLUE "📝 Creating environment configuration..."

cat > .env << EOF
# MommyShops Production Environment Configuration

# Database Configuration
DATABASE_URL=jdbc:postgresql://localhost:5432/mommyshops_prod
DATABASE_USERNAME=mommyshops
DATABASE_PASSWORD=mommyshops123

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1
OLLAMA_VISION_MODEL=llava

# API Keys (Please replace with your actual keys)
FDA_API_KEY=your_fda_api_key_here
EWG_API_KEY=your_ewg_api_key_here
INCI_BEAUTY_API_KEY=your_inci_beauty_api_key_here
COSING_API_KEY=your_cosing_api_key_here
ENTREZ_EMAIL=your.email@example.com
APIFY_API_KEY=your_apify_api_key_here

# Google OAuth (Please replace with your actual credentials)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# JWT Configuration
JWT_SECRET=your_jwt_secret_key_here
JWT_EXPIRATION=86400000

# Logging Configuration
LOG_LEVEL=INFO
BACKEND_LOG_PATH=logs/backend.log
LOG_MAX_FILE_SIZE=10MB
LOG_MAX_FILES=10

# CORS Configuration
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080

# Server Configuration
SERVER_PORT=8080
EOF

print_status $GREEN "✅ Environment configuration created"

# Create production configuration
print_status $BLUE "⚙️  Creating production configuration..."

cat > application-production.yml << EOF
# Production configuration for MommyShops
spring:
  profiles:
    active: production
  
  # Database configuration
  datasource:
    url: \${DATABASE_URL:jdbc:postgresql://localhost:5432/mommyshops_prod}
    username: \${DATABASE_USERNAME:mommyshops}
    password: \${DATABASE_PASSWORD:your_secure_password}
    driver-class-name: org.postgresql.Driver
    hikari:
      maximum-pool-size: 20
      minimum-idle: 5
      connection-timeout: 30000
      idle-timeout: 600000
      max-lifetime: 1800000
      leak-detection-threshold: 60000
  
  # JPA/Hibernate configuration
  jpa:
    hibernate:
      ddl-auto: validate
    show-sql: false
    properties:
      hibernate:
        dialect: org.hibernate.dialect.PostgreSQLDialect
        jdbc:
          batch_size: 25
        order_inserts: true
        order_updates: true
        batch_versioned_data: true
        connection:
          provider_disables_autocommit: true
        format_sql: false
        use_sql_comments: false
        jdbc:
          time_zone: UTC
  
  # Redis configuration
  redis:
    host: \${REDIS_HOST:localhost}
    port: \${REDIS_PORT:6379}
    password: \${REDIS_PASSWORD:}
    timeout: 2000ms
    lettuce:
      pool:
        max-active: 20
        max-idle: 10
        min-idle: 5
        max-wait: 2000ms

# Application configuration
app:
  # API configuration
  api:
    fda-key: \${FDA_API_KEY:}
    ewg-key: \${EWG_API_KEY:}
    inci-beauty-key: \${INCI_BEAUTY_API_KEY:}
    cosing-key: \${COSING_API_KEY:}
    entrez-email: \${ENTREZ_EMAIL:your.email@example.com}
    apify-key: \${APIFY_API_KEY:}
  
  # Ollama configuration
  ollama:
    base-url: \${OLLAMA_BASE_URL:http://localhost:11434}
    model: \${OLLAMA_MODEL:llama3.1}
    vision-model: \${OLLAMA_VISION_MODEL:llava}
    timeout: 30000
    max-retries: 3
  
  # Logging configuration
  logging:
    level: \${LOG_LEVEL:INFO}
    backend-path: \${BACKEND_LOG_PATH:logs/backend.log}
    max-file-size: \${LOG_MAX_FILE_SIZE:10MB}
    max-files: \${LOG_MAX_FILES:10}

# Server configuration
server:
  port: \${SERVER_PORT:8080}
  servlet:
    context-path: /
  compression:
    enabled: true
    mime-types: text/html,text/xml,text/plain,text/css,text/javascript,application/javascript,application/json
    min-response-size: 1024
  tomcat:
    max-connections: 8192
    max-threads: 200
    min-spare-threads: 10
    connection-timeout: 20000
    max-http-post-size: 2MB
    max-swallow-size: 2MB

# Management endpoints
management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics,prometheus
      base-path: /actuator
  endpoint:
    health:
      show-details: when_authorized
      show-components: always
  metrics:
    export:
      prometheus:
        enabled: true
    web:
      server:
        request:
          autotime:
            enabled: true

# Logging configuration
logging:
  level:
    com.mommyshops: \${LOG_LEVEL:INFO}
    org.springframework.security: WARN
    org.springframework.web: WARN
    org.hibernate.SQL: WARN
    org.hibernate.type.descriptor.sql.BasicBinder: WARN
  pattern:
    console: "%d{yyyy-MM-dd HH:mm:ss.SSS} [%thread] %-5level %logger{36} - %msg%n"
    file: "%d{yyyy-MM-dd HH:mm:ss.SSS} [%thread] %-5level %logger{36} - %msg%n"
  file:
    name: \${LOG_FILE_PATH:logs/mommyshops.log}
    max-size: \${LOG_MAX_FILE_SIZE:10MB}
    max-history: \${LOG_MAX_FILES:10}
    total-size-cap: \${LOG_TOTAL_SIZE_CAP:100MB}

# Vaadin configuration
vaadin:
  productionMode: true
  closeIdleSessions: true
  heartbeatInterval: 300
  webComponent:
    enabled: true
  frontend:
    hotdeploy: false
    bundle:
      enabled: true
      hash: true
      version: true
EOF

print_status $GREEN "✅ Production configuration created"

# Make scripts executable
print_status $BLUE "🔧 Making scripts executable..."
chmod +x start-production.sh
chmod +x stop-production.sh
chmod +x setup-jdk21.sh

print_status $GREEN "✅ Scripts made executable"

# Create systemd service file (Linux only)
if [ "$OS" = "linux" ]; then
    print_status $BLUE "🔧 Creating systemd service file..."
    
    sudo tee /etc/systemd/system/mommyshops.service > /dev/null << EOF
[Unit]
Description=MommyShops Application
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=SPRING_PROFILES_ACTIVE=production
ExecStart=/usr/bin/java -Xms512m -Xmx2g -XX:+UseG1GC -XX:+UseStringDeduplication -XX:+OptimizeStringConcat -jar target/mommyshops-app-*.jar
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    print_status $GREEN "✅ Systemd service file created"
fi

# Final verification
print_status $BLUE "🔍 Performing final verification..."

# Check Java
if command_exists java; then
    print_status $GREEN "✅ Java is available"
else
    print_status $RED "❌ Java is not available"
fi

# Check Maven
if command_exists mvn; then
    print_status $GREEN "✅ Maven is available"
else
    print_status $RED "❌ Maven is not available"
fi

# Check Docker
if command_exists docker; then
    print_status $GREEN "✅ Docker is available"
else
    print_status $RED "❌ Docker is not available"
fi

# Check Ollama
if command_exists ollama; then
    print_status $GREEN "✅ Ollama is available"
else
    print_status $RED "❌ Ollama is not available"
fi

# Check if Ollama is running
if curl -s http://localhost:11434/api/version >/dev/null 2>&1; then
    print_status $GREEN "✅ Ollama service is running"
else
    print_status $RED "❌ Ollama service is not running"
fi

print_status $GREEN "🎉 MommyShops production environment setup completed!"
print_status $BLUE "📋 Next steps:"
print_status $BLUE "1. Update the .env file with your actual API keys and credentials"
print_status $BLUE "2. Run: ./start-production.sh to start the application"
print_status $BLUE "3. Visit: http://localhost:8080 to access the application"
print_status $BLUE "4. Check health: http://localhost:8080/api/health"
print_status $BLUE "5. View logs: tail -f logs/mommyshops.log"
print_status $BLUE "6. Stop application: ./stop-production.sh"