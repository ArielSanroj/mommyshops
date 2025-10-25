#!/usr/bin/env python3
"""
Security test runner for MommyShops backend.
Runs comprehensive security tests and generates security report.
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SecurityTestRunner:
    """Security test runner for MommyShops"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.test_results = {
            "timestamp": time.time(),
            "tests": {},
            "security_scan": {},
            "coverage": {},
            "overall_status": "PENDING"
        }
    
    def run_security_tests(self):
        """Run comprehensive security tests"""
        logger.info("Starting security test suite...")
        
        try:
            # Run basic security tests
            self.run_basic_security_tests()
            
            # Run enhanced security tests
            self.run_enhanced_security_tests()
            
            # Run database security tests
            self.run_database_security_tests()
            
            # Run security configuration tests
            self.run_security_config_tests()
            
            # Run security scan
            self.run_security_scan()
            
            # Generate security report
            self.generate_security_report()
            
            # Determine overall status
            self.determine_overall_status()
            
            logger.info("Security test suite completed!")
            
        except Exception as e:
            logger.error(f"Security test suite failed: {e}")
            self.test_results["overall_status"] = "FAILED"
            raise
    
    def run_basic_security_tests(self):
        """Run basic security tests"""
        logger.info("Running basic security tests...")
        
        try:
            result = subprocess.run([
                "python", "-m", "pytest", "tests/test_security.py", "-v", "--tb=short"
            ], capture_output=True, text=True, cwd=self.project_root)
            
            self.test_results["tests"]["basic_security"] = {
                "status": "PASSED" if result.returncode == 0 else "FAILED",
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
            if result.returncode == 0:
                logger.info("Basic security tests passed!")
            else:
                logger.warning("Basic security tests failed!")
                
        except Exception as e:
            logger.error(f"Basic security tests failed: {e}")
            self.test_results["tests"]["basic_security"] = {
                "status": "FAILED",
                "error": str(e)
            }
    
    def run_enhanced_security_tests(self):
        """Run enhanced security tests"""
        logger.info("Running enhanced security tests...")
        
        try:
            result = subprocess.run([
                "python", "-m", "pytest", "tests/test_security_enhanced.py", "-v", "--tb=short"
            ], capture_output=True, text=True, cwd=self.project_root)
            
            self.test_results["tests"]["enhanced_security"] = {
                "status": "PASSED" if result.returncode == 0 else "FAILED",
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
            if result.returncode == 0:
                logger.info("Enhanced security tests passed!")
            else:
                logger.warning("Enhanced security tests failed!")
                
        except Exception as e:
            logger.error(f"Enhanced security tests failed: {e}")
            self.test_results["tests"]["enhanced_security"] = {
                "status": "FAILED",
                "error": str(e)
            }
    
    def run_database_security_tests(self):
        """Run database security tests"""
        logger.info("Running database security tests...")
        
        try:
            result = subprocess.run([
                "python", "-m", "pytest", "tests/test_database_security.py", "-v", "--tb=short"
            ], capture_output=True, text=True, cwd=self.project_root)
            
            self.test_results["tests"]["database_security"] = {
                "status": "PASSED" if result.returncode == 0 else "FAILED",
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
            if result.returncode == 0:
                logger.info("Database security tests passed!")
            else:
                logger.warning("Database security tests failed!")
                
        except Exception as e:
            logger.error(f"Database security tests failed: {e}")
            self.test_results["tests"]["database_security"] = {
                "status": "FAILED",
                "error": str(e)
            }
    
    def run_security_config_tests(self):
        """Run security configuration tests"""
        logger.info("Running security configuration tests...")
        
        try:
            # Test security configuration loading
            sys.path.insert(0, str(self.project_root / "backend-python"))
            from security_config import load_security_config, validate_security_config, get_security_level
            
            config = load_security_config()
            warnings = validate_security_config(config)
            security_level = get_security_level(config)
            
            self.test_results["tests"]["security_config"] = {
                "status": "PASSED",
                "security_level": security_level.value,
                "warnings": warnings,
                "config_loaded": True
            }
            
            logger.info(f"Security configuration loaded - Level: {security_level.value}")
            if warnings:
                logger.warning(f"Security configuration warnings: {warnings}")
                
        except Exception as e:
            logger.error(f"Security configuration tests failed: {e}")
            self.test_results["tests"]["security_config"] = {
                "status": "FAILED",
                "error": str(e)
            }
    
    def run_security_scan(self):
        """Run security scan"""
        logger.info("Running security scan...")
        
        security_scan_results = {
            "bandit": self.run_bandit_scan(),
            "safety": self.run_safety_scan(),
            "dependency_check": self.run_dependency_check()
        }
        
        self.test_results["security_scan"] = security_scan_results
        
        # Check if security scan passed
        all_passed = all(
            result.get("status") == "PASSED" 
            for result in security_scan_results.values()
        )
        
        if all_passed:
            logger.info("Security scan passed!")
        else:
            logger.warning("Security scan found issues!")
    
    def run_bandit_scan(self):
        """Run Bandit security linter"""
        try:
            result = subprocess.run([
                "bandit", "-r", "backend-python/", "-f", "json"
            ], capture_output=True, text=True, cwd=self.project_root)
            
            return {
                "status": "PASSED" if result.returncode == 0 else "FAILED",
                "returncode": result.returncode,
                "output": result.stdout
            }
            
        except Exception as e:
            return {
                "status": "FAILED",
                "error": str(e)
            }
    
    def run_safety_scan(self):
        """Run Safety dependency check"""
        try:
            result = subprocess.run([
                "safety", "check", "--json"
            ], capture_output=True, text=True, cwd=self.project_root)
            
            return {
                "status": "PASSED" if result.returncode == 0 else "FAILED",
                "returncode": result.returncode,
                "output": result.stdout
            }
            
        except Exception as e:
            return {
                "status": "FAILED",
                "error": str(e)
            }
    
    def run_dependency_check(self):
        """Run dependency security check"""
        try:
            result = subprocess.run([
                "pip", "audit"
            ], capture_output=True, text=True, cwd=self.project_root)
            
            return {
                "status": "PASSED" if result.returncode == 0 else "FAILED",
                "returncode": result.returncode,
                "output": result.stdout
            }
            
        except Exception as e:
            return {
                "status": "FAILED",
                "error": str(e)
            }
    
    def generate_security_report(self):
        """Generate comprehensive security report"""
        logger.info("Generating security report...")
        
        try:
            sys.path.insert(0, str(self.project_root / "backend-python"))
            from security_config import get_security_config, generate_security_report
            
            config = get_security_config()
            report = generate_security_report(config)
            
            self.test_results["security_report"] = report
            
            # Save report to file
            report_path = self.project_root / "security_report.json"
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Security report saved to: {report_path}")
            
        except Exception as e:
            logger.error(f"Failed to generate security report: {e}")
            self.test_results["security_report"] = {"error": str(e)}
    
    def determine_overall_status(self):
        """Determine overall security test status"""
        all_tests_passed = all(
            result.get("status") == "PASSED" 
            for result in self.test_results["tests"].values()
        )
        
        all_scans_passed = all(
            result.get("status") == "PASSED" 
            for result in self.test_results["security_scan"].values()
        )
        
        if all_tests_passed and all_scans_passed:
            self.test_results["overall_status"] = "PASSED"
            logger.info("Overall security test status: PASSED")
        else:
            self.test_results["overall_status"] = "FAILED"
            logger.warning("Overall security test status: FAILED")
    
    def print_summary(self):
        """Print security test summary"""
        print("\n" + "="*60)
        print("SECURITY TEST SUMMARY")
        print("="*60)
        print(f"Overall Status: {self.test_results['overall_status']}")
        print(f"Timestamp: {time.ctime(self.test_results['timestamp'])}")
        
        print("\nTest Results:")
        for test_name, result in self.test_results["tests"].items():
            status = result.get("status", "UNKNOWN")
            print(f"  {test_name}: {status}")
        
        print("\nSecurity Scan Results:")
        for scan_name, result in self.test_results["security_scan"].items():
            status = result.get("status", "UNKNOWN")
            print(f"  {scan_name}: {status}")
        
        if "security_report" in self.test_results:
            report = self.test_results["security_report"]
            if "security_level" in report:
                print(f"\nSecurity Level: {report['security_level']}")
            if "warnings" in report:
                print(f"Warnings: {len(report['warnings'])}")
        
        print("="*60)

def main():
    """Main security test runner"""
    project_root = "/workspaces/mommyshops"
    runner = SecurityTestRunner(project_root)
    
    try:
        runner.run_security_tests()
        runner.print_summary()
        
        # Exit with appropriate code
        if runner.test_results["overall_status"] == "PASSED":
            sys.exit(0)
        else:
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Security test runner failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
