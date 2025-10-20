# 🚀 MommyShops Runtime Setup Guide

This guide will help you set up the complete runtime environment to test image analysis with `test3.jpg`.

## 📋 Prerequisites

- macOS (with Homebrew)
- Java 21+
- Maven 3.6+
- PostgreSQL
- Ollama (AI models)

## 🎯 Quick Start (3 Commands)

```bash
# 1. Set up database
./scripts/setup-database.sh

# 2. Set up Ollama with AI models
./scripts/setup-ollama-complete.sh

# 3. Start the application
./scripts/start-application.sh
```

## 📁 Test Image Setup

1. Place your test image in the `mommyshops-app` directory
2. Rename it to `test3.jpg`
3. Run the complete test: `./scripts/test-complete-flow.sh`

## 🔧 Detailed Setup Steps

### Step 1: Database Setup
```bash
./scripts/setup-database.sh
```
**What it does:**
- Installs PostgreSQL (if needed)
- Creates `mommyshops` database
- Creates `mommyshops` user with password `change-me`
- Tests database connection

### Step 2: Ollama AI Setup
```bash
./scripts/setup-ollama-complete.sh
```
**What it does:**
- Installs Ollama (if needed)
- Starts Ollama service
- Downloads required AI models:
  - `llama3.1` (text generation)
  - `llava` (vision model for image analysis)
  - `llama3.1:8b` (faster model)
- Tests AI functionality

### Step 3: Application Startup
```bash
./scripts/start-application.sh
```
**What it does:**
- Checks all dependencies
- Compiles the application
- Starts Spring Boot on port 8080
- Configures environment variables

## 🧪 Testing the Complete Flow

### Automated Test
```bash
./scripts/test-complete-flow.sh
```
**What it tests:**
- All service dependencies
- Ollama health and models
- Database connectivity
- Direct vision analysis of test3.jpg
- Application health endpoints

### Manual Testing
1. **Open browser:** http://localhost:8080/analysis
2. **Upload image:** Drag & drop `test3.jpg`
3. **Enter product name:** e.g., "Test Shampoo"
4. **Click "Analizar imagen"**
5. **Wait for AI analysis** (may take 30-60 seconds)
6. **Review results:** Safety scores, recommendations, alternatives

## 🌐 Application Endpoints

| Endpoint | Description |
|----------|-------------|
| http://localhost:8080 | Main application |
| http://localhost:8080/analysis | Image analysis page |
| http://localhost:8080/actuator/health | Application health |
| http://localhost:8080/api/ollama/health | Ollama health check |
| http://localhost:8080/api/ollama/models | Available AI models |

## 🔍 Troubleshooting

### Common Issues

#### 1. PostgreSQL Connection Failed
```bash
# Check if PostgreSQL is running
brew services list | grep postgresql

# Start PostgreSQL
brew services start postgresql

# Test connection
psql -h localhost -U mommyshops -d mommyshops -c "SELECT 1;"
```

#### 2. Ollama Not Running
```bash
# Start Ollama
ollama serve

# Check if models are loaded
ollama list

# Pull missing models
ollama pull llama3.1
ollama pull llava
```

#### 3. Application Won't Start
```bash
# Check compilation
mvn clean compile

# Check dependencies
mvn dependency:tree

# Check logs
mvn spring-boot:run -X
```

#### 4. Image Analysis Fails
- **Check browser console** for JavaScript errors
- **Verify image format** (JPG, PNG supported)
- **Check Ollama health** at http://localhost:8080/api/ollama/health
- **Try smaller image** (under 10MB)

### Debug Mode

Enable debug logging in `application.properties`:
```properties
logging.level.com.mommyshops=DEBUG
logging.level.org.springframework.web.reactive.function.client=DEBUG
```

## 📊 Expected Results

When testing with `test3.jpg`, you should see:

1. **Image Upload:** ✅ Status shows "Imagen cargada"
2. **OCR Processing:** AI extracts ingredient list from image
3. **AI Analysis:** Each ingredient analyzed for safety
4. **Results Display:**
   - Overall safety score (0-100)
   - Eco-friendliness score (0-100)
   - Risk flags and warnings
   - Substitute recommendations
   - Detailed analysis text

## 🎯 Success Criteria

The setup is successful when:
- ✅ All scripts run without errors
- ✅ Application starts on port 8080
- ✅ Image upload works in browser
- ✅ AI analysis completes successfully
- ✅ Results are displayed with safety scores

## 🔧 Configuration

### Environment Variables
```bash
# Ollama Configuration
export OLLAMA_BASE_URL=http://localhost:11434
export OLLAMA_MODEL=llama3.1
export OLLAMA_VISION_MODEL=llava

# Database Configuration
export SPRING_DATASOURCE_URL=jdbc:postgresql://localhost:5432/mommyshops
export SPRING_DATASOURCE_USERNAME=mommyshops
export SPRING_DATASOURCE_PASSWORD=change-me
```

### Application Properties
The application uses these default configurations:
- **File upload limit:** 10MB
- **Ollama timeout:** 120 seconds
- **Analysis confidence threshold:** 70%
- **Max ingredients:** 50

## 🚀 Performance Tips

1. **Use smaller models** for faster processing:
   ```bash
   export OLLAMA_MODEL=llama3.1:8b
   ```

2. **Optimize images** before upload:
   - Resize to reasonable dimensions
   - Compress if needed
   - Ensure good contrast for OCR

3. **Monitor resources:**
   - Ollama uses significant RAM
   - PostgreSQL needs disk space
   - Spring Boot needs JVM memory

## 📞 Support

If you encounter issues:

1. **Check logs** in the terminal running the application
2. **Verify all services** are running with the test script
3. **Check browser console** for frontend errors
4. **Review this guide** for troubleshooting steps

---

**Ready to test image analysis with test3.jpg!** 🎉