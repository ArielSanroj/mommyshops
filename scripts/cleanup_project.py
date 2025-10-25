#!/usr/bin/env python3
"""
Project cleanup script for MommyShops
Removes duplicate files, organizes structure, and cleans up outdated files
"""

import os
import shutil
import glob
import json
from pathlib import Path
from typing import List, Dict, Any
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProjectCleanup:
    """Project cleanup and organization"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.backup_dir = self.project_root / "backup_cleanup"
        self.cleanup_log = []
        
    def run_cleanup(self):
        """Run complete project cleanup"""
        logger.info("Starting project cleanup...")
        
        # Create backup directory
        self.backup_dir.mkdir(exist_ok=True)
        
        # Cleanup steps
        self.cleanup_duplicate_files()
        self.cleanup_outdated_files()
        self.cleanup_temp_files()
        self.cleanup_old_backups()
        self.organize_project_structure()
        self.cleanup_dependencies()
        self.generate_cleanup_report()
        
        logger.info("Project cleanup completed!")
    
    def cleanup_duplicate_files(self):
        """Remove duplicate files"""
        logger.info("Cleaning up duplicate files...")
        
        # Files to remove (duplicates or outdated)
        files_to_remove = [
            "backend/",  # Old backend directory
            "config/",   # Old config directory
            "ml/",       # Old ML directory
            "markdown/", # Old markdown directory
            "tests-shared/", # Duplicate tests
            "dev_sqlite.db",
            "image_base64.txt",
            "test2.jpg",
            "test3.jpg",
            "test_frontend_display.html",
            "test_endpoint.sh",
            "restart.sh",
            "start_app.sh",
            "run_backend.sh",
            "fix_dependencies.sh",
            "get_helm.sh",
            "setup_new_mac.sh",
            "export_project.sh",
            "railway.env",
            "railway.toml",
            "runtime.txt",
            "requirements_streamlit.txt",
            "llama-31-8b-instruct.yaml",
            "firebase-service-account.json.example",
            "firestore.rules",
            "config.yaml",
            "cosmetic_ingredients_lexicon.txt",
            "Dockerfile",  # Old root Dockerfile
            "docker-compose.yml",  # Old docker-compose
            "docker-compose.ollama.yml",  # Old docker-compose
            "mvnw",
            "mvnw.cmd",
            "pyproject.toml",  # Old pyproject.toml
        ]
        
        for file_path in files_to_remove:
            full_path = self.project_root / file_path
            if full_path.exists():
                if full_path.is_dir():
                    shutil.rmtree(full_path)
                    logger.info(f"Removed directory: {file_path}")
                else:
                    full_path.unlink()
                    logger.info(f"Removed file: {file_path}")
                
                self.cleanup_log.append(f"Removed: {file_path}")
    
    def cleanup_outdated_files(self):
        """Remove outdated files"""
        logger.info("Cleaning up outdated files...")
        
        # Remove old cache files
        cache_patterns = [
            "**/__pycache__",
            "**/*.pyc",
            "**/*.pyo",
            "**/*.pyd",
            "**/.pytest_cache",
            "**/node_modules",
            "**/.mypy_cache",
            "**/.coverage",
            "**/htmlcov",
            "**/.tox",
            "**/.venv",
            "**/venv",
            "**/env",
            "**/.env.local",
            "**/.env.development.local",
            "**/.env.test.local",
            "**/.env.production.local",
        ]
        
        for pattern in cache_patterns:
            for file_path in glob.glob(str(self.project_root / pattern), recursive=True):
                path = Path(file_path)
                if path.exists():
                    if path.is_dir():
                        shutil.rmtree(path)
                        logger.info(f"Removed cache directory: {path.relative_to(self.project_root)}")
                    else:
                        path.unlink()
                        logger.info(f"Removed cache file: {path.relative_to(self.project_root)}")
                    
                    self.cleanup_log.append(f"Removed cache: {path.relative_to(self.project_root)}")
    
    def cleanup_temp_files(self):
        """Remove temporary files"""
        logger.info("Cleaning up temporary files...")
        
        # Temporary file patterns
        temp_patterns = [
            "**/*.tmp",
            "**/*.temp",
            "**/*.log",
            "**/*.pid",
            "**/*.lock",
            "**/.DS_Store",
            "**/Thumbs.db",
            "**/*.swp",
            "**/*.swo",
            "**/*~",
            "**/.fuse_hidden*",
            "**/nohup.out",
            "**/*.orig",
            "**/*.rej",
        ]
        
        for pattern in temp_patterns:
            for file_path in glob.glob(str(self.project_root / pattern), recursive=True):
                path = Path(file_path)
                if path.exists():
                    path.unlink()
                    logger.info(f"Removed temp file: {path.relative_to(self.project_root)}")
                    self.cleanup_log.append(f"Removed temp: {path.relative_to(self.project_root)}")
    
    def cleanup_old_backups(self):
        """Remove old backup files"""
        logger.info("Cleaning up old backup files...")
        
        # Backup file patterns
        backup_patterns = [
            "**/*.bak",
            "**/*.backup",
            "**/*.old",
            "**/*.orig",
            "**/*.save",
            "**/*.swp",
            "**/*.tmp",
        ]
        
        for pattern in backup_patterns:
            for file_path in glob.glob(str(self.project_root / pattern), recursive=True):
                path = Path(file_path)
                if path.exists():
                    path.unlink()
                    logger.info(f"Removed backup file: {path.relative_to(self.project_root)}")
                    self.cleanup_log.append(f"Removed backup: {path.relative_to(self.project_root)}")
    
    def organize_project_structure(self):
        """Organize project structure"""
        logger.info("Organizing project structure...")
        
        # Create organized directory structure
        directories = [
            "backend-python/core",
            "backend-python/api/routes",
            "backend-python/services",
            "backend-python/models",
            "backend-python/utils",
            "backend-java/src/main/java/com/mommyshops",
            "backend-java/src/main/resources",
            "backend-java/src/test/java/com/mommyshops",
            "tests/unit",
            "tests/integration",
            "tests/e2e",
            "docs/api",
            "docs/architecture",
            "docs/deployment",
            "scripts/setup",
            "scripts/deployment",
            "scripts/maintenance",
            "monitoring/grafana",
            "monitoring/prometheus",
            "monitoring/alertmanager",
        ]
        
        for directory in directories:
            dir_path = self.project_root / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {directory}")
    
    def cleanup_dependencies(self):
        """Clean up dependency files"""
        logger.info("Cleaning up dependency files...")
        
        # Remove old dependency files
        old_deps = [
            "requirements_streamlit.txt",
            "requirements.txt",  # Old requirements
            "pyproject.toml",   # Old pyproject
        ]
        
        for dep_file in old_deps:
            dep_path = self.project_root / dep_file
            if dep_path.exists():
                dep_path.unlink()
                logger.info(f"Removed old dependency file: {dep_file}")
                self.cleanup_log.append(f"Removed old deps: {dep_file}")
    
    def generate_cleanup_report(self):
        """Generate cleanup report"""
        logger.info("Generating cleanup report...")
        
        report = {
            "cleanup_date": str(Path.cwd()),
            "files_removed": len(self.cleanup_log),
            "cleanup_log": self.cleanup_log,
            "project_structure": self.get_project_structure()
        }
        
        report_path = self.project_root / "cleanup_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Cleanup report saved to: {report_path}")
    
    def get_project_structure(self) -> Dict[str, Any]:
        """Get current project structure"""
        structure = {}
        
        for root, dirs, files in os.walk(self.project_root):
            # Skip hidden directories and cache directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
            
            rel_root = Path(root).relative_to(self.project_root)
            if str(rel_root) == '.':
                continue
            
            structure[str(rel_root)] = {
                'directories': dirs,
                'files': [f for f in files if not f.startswith('.')]
            }
        
        return structure

def main():
    """Main cleanup function"""
    project_root = "/workspaces/mommyshops"
    cleanup = ProjectCleanup(project_root)
    cleanup.run_cleanup()

if __name__ == "__main__":
    main()
