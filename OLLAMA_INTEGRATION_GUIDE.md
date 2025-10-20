# Ollama Integration Guide for MommyShops

This guide provides complete instructions for integrating Ollama with your MommyShops application for local AI-powered cosmetic analysis.

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)
```bash
# Run the automated setup script
./scripts/setup-ollama.sh
```

### Option 2: Manual Setup
Follow the step-by-step instructions below.

## 📋 Prerequisites

- macOS, Linux, or Windows with WSL
- Docker (optional, for containerized setup)
- Java 21+
- Maven 3.6+

## 🔧 Installation Steps

### 1. Install Ollama

#### macOS/Linux:
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

#### Windows (WSL):
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### 2. Start Ollama Service

```bash
# Start Ollama in the background
ollama serve &

# Or start in foreground (keep terminal open)
ollama serve
```

### 3. Pull Required Models

```bash
# Pull the main language model
ollama pull llama3.1

# Pull the vision model for image analysis
ollama pull llava

# Verify models are installed
ollama list
```

### 4. Configure Environment Variables

Create a `.env` file in your project root:

```bash
# Ollama Configuration
export OLLAMA_BASE_URL=http://localhost:11434
export OLLAMA_MODEL=llama3.1
export OLLAMA_VISION_MODEL=llava
```

Or add to your shell profile (`~/.bashrc`, `~/.zshrc`):

```bash
echo 'export OLLAMA_BASE_URL=http://localhost:11434' >> ~/.zshrc
echo 'export OLLAMA_MODEL=llama3.1' >> ~/.zshrc
echo 'export OLLAMA_VISION_MODEL=llava' >> ~/.zshrc
source ~/.zshrc
```

### 5. Update Application Configuration

The application is already configured with these properties in `application.properties`:

```properties
# Ollama Configuration
ollama.base-url=${OLLAMA_BASE_URL:http://localhost:11434}
ollama.model=${OLLAMA_MODEL:llama3.1}
ollama.timeout=120
```

## 🧪 Testing the Integration

### 1. Start Your Application

```bash
# Make sure environment variables are loaded
source .env

# Start the Spring Boot application
./mvnw spring-boot:run
```

### 2. Test Ollama Connectivity

```bash
# Test Ollama health endpoint
curl http://localhost:8080/api/ollama/health

# Test Ollama models endpoint
curl http://localhost:8080/api/ollama/models

# Test general application health
curl http://localhost:8080/actuator/health
```

### 3. Test Direct Ollama API

```bash
# Test Ollama directly
curl http://localhost:11434/api/tags

# Test a simple generation
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1",
    "prompt": "Hello, how are you?",
    "stream": false
  }'
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Ollama Service Not Starting
```bash
# Check if Ollama is running
ps aux | grep ollama

# Check Ollama logs
ollama logs

# Restart Ollama
pkill ollama
ollama serve &
```

#### 2. Models Not Found
```bash
# List installed models
ollama list

# Pull missing models
ollama pull llama3.1
ollama pull llava

# Check available models
ollama search llama
```

#### 3. Connection Refused
```bash
# Check if port 11434 is open
netstat -an | grep 11434

# Test connectivity
curl -v http://localhost:11434/api/tags
```

#### 4. Application Can't Connect
- Verify environment variables are set: `echo $OLLAMA_BASE_URL`
- Check application logs for connection errors
- Ensure Ollama is running before starting the application
- Verify firewall settings allow local connections

### Debug Mode

Enable debug logging in `application.properties`:

```properties
# Debug logging
logging.level.com.mommyshops.ai=DEBUG
logging.level.org.springframework.web.reactive.function.client=DEBUG
```

## 🏗️ Architecture Overview

### Components

1. **OllamaService**: Main service for AI interactions
2. **OllamaHealthController**: Health check endpoints
3. **WebClientConfig**: HTTP client configuration
4. **Application Properties**: Configuration management

### Data Flow

```
User Request → OllamaService → Ollama API → JSON Response → Parsed Analysis
```

### Key Features

- ✅ Reactive HTTP client with WebFlux
- ✅ JSON response parsing with Jackson
- ✅ Error handling and fallbacks
- ✅ Health check endpoints
- ✅ Configurable timeouts
- ✅ Model selection via environment variables

## 🔧 Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3.1` | Text generation model |
| `OLLAMA_VISION_MODEL` | `llava` | Image analysis model |

### Application Properties

| Property | Default | Description |
|----------|---------|-------------|
| `ollama.base-url` | `${OLLAMA_BASE_URL:http://localhost:11434}` | Ollama server URL |
| `ollama.model` | `${OLLAMA_MODEL:llama3.1}` | Text generation model |
| `ollama.timeout` | `120` | Request timeout in seconds |

## 🚀 Production Considerations

### Security
- Ollama runs locally, no external API keys needed
- Ensure proper firewall configuration
- Consider running Ollama in a container for isolation

### Performance
- Monitor memory usage (models can be large)
- Consider model quantization for smaller memory footprint
- Use appropriate timeout values for your use case

### Monitoring
- Health check endpoints available at `/api/ollama/health`
- Application metrics include Ollama connectivity status
- Logs include request/response details in debug mode

## 📚 Additional Resources

- [Ollama Documentation](https://ollama.ai/docs)
- [Ollama Model Library](https://ollama.ai/library)
- [Spring WebFlux Documentation](https://docs.spring.io/spring-framework/docs/current/reference/html/web-reactive.html)
- [Jackson JSON Processing](https://github.com/FasterXML/jackson)

## 🆘 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review application logs with debug logging enabled
3. Test Ollama connectivity independently
4. Verify all environment variables are properly set
5. Ensure models are installed and accessible

---

**Note**: This integration provides local AI capabilities without requiring external API keys or internet connectivity for AI operations. All processing happens on your local machine.