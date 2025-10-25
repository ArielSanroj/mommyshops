#!/usr/bin/env python3
"""
Migration script to convert monolithic main.py to modular structure
"""

import os
import sys
import shutil
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def backup_original_file(file_path: Path) -> Path:
    """Create backup of original file"""
    backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
    shutil.copy2(file_path, backup_path)
    logger.info(f"📁 Backed up {file_path} to {backup_path}")
    return backup_path

def create_modular_structure(root_path: Path):
    """Create modular directory structure"""
    logger.info("🏗️ Creating modular directory structure...")
    
    # Create directories
    directories = [
        "backend-python/app",
        "backend-python/app/middleware",
        "backend-python/app/routers", 
        "backend-python/app/services",
        "backend-python/migrations",
        "backend-python/migrations/versions",
        "tests/functional",
        "tests/performance"
    ]
    
    for directory in directories:
        dir_path = root_path / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 Created directory: {directory}")

def update_imports_in_main():
    """Update imports in main.py to use modular structure"""
    logger.info("🔄 Updating imports in main.py...")
    
    # This would be done manually or with more sophisticated parsing
    # For now, we'll create a new main.py that imports from the modular structure
    pass

def create_startup_script():
    """Create startup script for the new modular structure"""
    startup_script = """#!/bin/bash
# MommyShops Startup Script

echo "🚀 Starting MommyShops application..."

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)/backend-python"
export DATABASE_URL="${DATABASE_URL:-postgresql://mommyshops:password@localhost:5432/mommyshops}"
export REDIS_HOST="${REDIS_HOST:-localhost}"
export REDIS_PORT="${REDIS_PORT:-6379}"
export JWT_SECRET="${JWT_SECRET:-your-secret-key-here}"

# Run database migrations
echo "📊 Running database migrations..."
cd backend-python
alembic upgrade head

# Start the application
echo "🌟 Starting FastAPI application..."
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
"""
    
    return startup_script

def create_docker_compose_update():
    """Create updated docker-compose.yml for modular structure"""
    docker_compose = """version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: mommyshops
      POSTGRES_USER: mommyshops
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  python-backend:
    build: ./backend-python
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://mommyshops:password@postgres:5432/mommyshops
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - JWT_SECRET=your-secret-key-here
    depends_on:
      - postgres
      - redis
    volumes:
      - ./backend-python:/app
    command: >
      sh -c "
        alembic upgrade head &&
        python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
      "

  java-backend:
    build: ./backend-java
    ports:
      - "8080:8080"
    environment:
      - SPRING_DATASOURCE_URL=jdbc:postgresql://postgres:5432/mommyshops
      - SPRING_DATASOURCE_USERNAME=mommyshops
      - SPRING_DATASOURCE_PASSWORD=password
    depends_on:
      - postgres
    volumes:
      - ./backend-java:/app

volumes:
  postgres_data:
  redis_data:
"""
    
    return docker_compose

def create_migration_guide():
    """Create migration guide"""
    guide = """# Migration Guide: Monolithic to Modular Structure

## Overview
This guide helps you migrate from the monolithic `main.py` to the new modular structure.

## What Changed

### 1. Directory Structure
```
backend-python/
├── app/
│   ├── __init__.py
│   ├── main.py              # New modular main.py
│   ├── dependencies.py      # Shared dependencies
│   ├── middleware/          # Middleware modules
│   │   ├── __init__.py
│   │   ├── cors.py
│   │   ├── security.py
│   │   ├── logging.py
│   │   └── rate_limiting.py
│   ├── routers/             # API routers
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── analysis.py
│   │   ├── health.py
│   │   └── admin.py
│   └── services/            # Business logic services
│       ├── __init__.py
│       ├── analysis_service.py
│       ├── ocr_service.py
│       └── ingredient_service.py
├── migrations/              # Database migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 001_initial_schema.py
└── alembic.ini
```

### 2. Key Benefits
- **Modularity**: Each component has a single responsibility
- **Maintainability**: Easier to find and modify specific functionality
- **Testability**: Individual components can be tested in isolation
- **Scalability**: Components can be scaled independently
- **Database Migrations**: Proper version control for database schema

### 3. Migration Steps

#### Step 1: Backup Original Files
```bash
cp backend-python/main.py backend-python/main.py.backup
```

#### Step 2: Update Imports
The new modular structure uses relative imports:
```python
# Old (monolithic)
from database import get_db, User

# New (modular)
from app.dependencies import get_database, require_auth
from database import User
```

#### Step 3: Update Startup
```bash
# Old
python main.py

# New
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### Step 4: Database Migrations
```bash
cd backend-python
alembic upgrade head
```

### 4. Testing the Migration

#### Run Tests
```bash
# Run all tests
python scripts/run_comprehensive_tests.py

# Run specific test suites
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/functional/ -v
```

#### Verify Functionality
```bash
# Start the application
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Test endpoints
curl http://localhost:8000/health/
curl http://localhost:8000/docs
```

### 5. Rollback Plan
If issues occur, you can rollback:
```bash
# Restore original main.py
cp backend-python/main.py.backup backend-python/main.py

# Revert database migrations (if needed)
alembic downgrade -1
```

### 6. Next Steps
1. **Review the new structure** and understand the separation of concerns
2. **Update your deployment scripts** to use the new startup command
3. **Update your documentation** to reflect the new structure
4. **Train your team** on the new modular architecture
5. **Consider further refactoring** based on your specific needs

## Support
If you encounter issues during migration, check:
1. All dependencies are installed
2. Database connection is working
3. Environment variables are set correctly
4. All tests are passing

For additional help, refer to the comprehensive documentation in the `docs/` directory.
"""
    
    return guide

def main():
    """Main migration function"""
    logger.info("🚀 Starting migration to modular structure...")
    
    # Get root path
    if len(sys.argv) > 1:
        root_path = Path(sys.argv[1])
    else:
        root_path = Path(".")
    
    # Create modular structure
    create_modular_structure(root_path)
    
    # Create startup script
    startup_script = create_startup_script()
    startup_file = root_path / "startup.sh"
    with open(startup_file, "w") as f:
        f.write(startup_script)
    os.chmod(startup_file, 0o755)
    logger.info(f"📝 Created startup script: {startup_file}")
    
    # Create updated docker-compose
    docker_compose = create_docker_compose_update()
    docker_file = root_path / "docker-compose.modular.yml"
    with open(docker_file, "w") as f:
        f.write(docker_compose)
    logger.info(f"🐳 Created updated docker-compose: {docker_file}")
    
    # Create migration guide
    guide = create_migration_guide()
    guide_file = root_path / "MIGRATION_GUIDE.md"
    with open(guide_file, "w") as f:
        f.write(guide)
    logger.info(f"📖 Created migration guide: {guide_file}")
    
    logger.info("✅ Migration preparation complete!")
    logger.info("📋 Next steps:")
    logger.info("1. Review the new modular structure")
    logger.info("2. Update your deployment scripts")
    logger.info("3. Test the new structure")
    logger.info("4. Follow the migration guide")

if __name__ == "__main__":
    main()
