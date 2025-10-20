#!/bin/bash

# Setup script for JDK 21 and MommyShops development environment
# This script ensures the correct Java runtime is installed and configured

echo "🚀 Setting up MommyShops development environment with JDK 21..."

# Check if we're on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "📱 Detected macOS system"
    
    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        echo "❌ Homebrew is not installed. Please install Homebrew first:"
        echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi
    
    # Install JDK 21 using Homebrew
    echo "☕ Installing OpenJDK 21..."
    brew install openjdk@21
    
    # Set JAVA_HOME
    echo "🔧 Setting JAVA_HOME..."
    export JAVA_HOME=$(/usr/libexec/java_home -v 21)
    echo "JAVA_HOME set to: $JAVA_HOME"
    
    # Add to shell profile
    echo "📝 Adding JAVA_HOME to shell profile..."
    echo 'export JAVA_HOME=$(/usr/libexec/java_home -v 21)' >> ~/.zshrc
    echo 'export PATH=$JAVA_HOME/bin:$PATH' >> ~/.zshrc
    
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "🐧 Detected Linux system"
    
    # Update package list
    sudo apt update
    
    # Install OpenJDK 21
    echo "☕ Installing OpenJDK 21..."
    sudo apt install -y openjdk-21-jdk
    
    # Set JAVA_HOME
    echo "🔧 Setting JAVA_HOME..."
    export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
    echo "JAVA_HOME set to: $JAVA_HOME"
    
    # Add to shell profile
    echo "📝 Adding JAVA_HOME to shell profile..."
    echo 'export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64' >> ~/.bashrc
    echo 'export PATH=$JAVA_HOME/bin:$PATH' >> ~/.bashrc
    
else
    echo "❌ Unsupported operating system: $OSTYPE"
    echo "Please install JDK 21 manually and set JAVA_HOME"
    exit 1
fi

# Verify Java installation
echo "✅ Verifying Java installation..."
java -version
javac -version

# Check Maven
echo "🔍 Checking Maven installation..."
if command -v mvn &> /dev/null; then
    mvn -version
else
    echo "❌ Maven is not installed. Please install Maven:"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "   brew install maven"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "   sudo apt install maven"
    fi
    exit 1
fi

# Check Docker (for Testcontainers)
echo "🐳 Checking Docker installation..."
if command -v docker &> /dev/null; then
    docker --version
    echo "✅ Docker is available for Testcontainers"
else
    echo "⚠️  Docker is not installed. Testcontainers tests will not work without Docker."
    echo "   Please install Docker Desktop: https://www.docker.com/products/docker-desktop"
fi

# Check Ollama (for AI features)
echo "🤖 Checking Ollama installation..."
if command -v ollama &> /dev/null; then
    ollama --version
    echo "✅ Ollama is available for AI features"
else
    echo "⚠️  Ollama is not installed. AI features will use mock services."
    echo "   To install Ollama: https://ollama.ai/download"
fi

# Set up environment variables
echo "🔧 Setting up environment variables..."
cat > .env << EOF
# MommyShops Environment Configuration

# Database Configuration
SPRING_DATASOURCE_URL=jdbc:postgresql://localhost:5432/mommyshops
SPRING_DATASOURCE_USERNAME=mommyshops
SPRING_DATASOURCE_PASSWORD=mommyshops

# Redis Configuration
SPRING_DATA_REDIS_HOST=localhost
SPRING_DATA_REDIS_PORT=6379

# External API Keys (replace with your actual keys)
EXTERNAL_API_FDA_KEY=your_fda_api_key_here
EXTERNAL_API_EWG_KEY=your_ewg_api_key_here
EXTERNAL_API_INCI_BEAUTY_KEY=your_inci_beauty_api_key_here
EXTERNAL_API_COSING_KEY=your_cosing_api_key_here

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1
OLLAMA_VISION_MODEL=llava

# Security Configuration (for development)
SPRING_SECURITY_OAUTH2_CLIENT_REGISTRATION_GOOGLE_CLIENT_ID=your_google_client_id
SPRING_SECURITY_OAUTH2_CLIENT_REGISTRATION_GOOGLE_CLIENT_SECRET=your_google_client_secret
EOF

echo "📄 Created .env file with environment variables"

# Create test database
echo "🗄️  Setting up test database..."
if command -v psql &> /dev/null; then
    echo "PostgreSQL client is available"
else
    echo "⚠️  PostgreSQL client is not available. Please install PostgreSQL:"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "   brew install postgresql"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "   sudo apt install postgresql-client"
    fi
fi

# Test Maven compilation first
echo "🧪 Testing Maven compilation..."
if mvn clean compile -q; then
    echo "✅ Maven compilation successful!"
else
    echo "❌ Maven compilation failed. Please check the error messages above."
    exit 1
fi

# Run tests to verify setup
echo "🧪 Running tests to verify setup..."
if mvn test -Dtest="MommyshopsApplicationTests" -q; then
    echo "✅ Basic tests passed! Setup is working correctly."
else
    echo "❌ Tests failed. Please check the error messages above."
    exit 1
fi

echo ""
echo "🎉 Setup complete! MommyShops development environment is ready."
echo ""
echo "📋 Next steps:"
echo "1. Update the .env file with your actual API keys"
echo "2. Start PostgreSQL and Redis services"
echo "3. Run 'mvn spring-boot:run' to start the application"
echo "4. Run 'mvn test' to run all tests"
echo ""
echo "🔗 Useful commands:"
echo "  mvn clean install          # Build the project"
echo "  mvn test                   # Run all tests"
echo "  mvn spring-boot:run        # Start the application"
echo "  mvn test -Dtest=*Test      # Run specific tests"
echo ""
echo "📚 Documentation:"
echo "  - README.md                # Project overview"
echo "  - TESTING_IMPLEMENTATION_SUMMARY.md  # Testing documentation"
echo "  - FINAL_IMPLEMENTATION_SUMMARY.md    # Implementation details"
echo ""
echo "Happy coding! 🚀"