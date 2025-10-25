#!/usr/bin/env python3
"""
Comprehensive Test Runner
Runs all tests with coverage reporting and analysis
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path
from typing import Dict, List, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComprehensiveTestRunner:
    """Comprehensive test runner with coverage analysis"""
    
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.results = {
            "python": {"passed": 0, "failed": 0, "skipped": 0, "coverage": 0.0},
            "java": {"passed": 0, "failed": 0, "skipped": 0, "coverage": 0.0},
            "integration": {"passed": 0, "failed": 0, "skipped": 0},
            "e2e": {"passed": 0, "failed": 0, "skipped": 0},
            "security": {"passed": 0, "failed": 0, "skipped": 0},
            "performance": {"passed": 0, "failed": 0, "skipped": 0}
        }
    
    def run_python_tests(self) -> bool:
        """Run Python tests with coverage"""
        logger.info("🐍 Running Python tests...")
        
        try:
            # Unit tests
            result = subprocess.run([
                "pytest", "tests/unit/", "-v", "--cov=app", "--cov-report=xml", "--cov-report=html"
            ], cwd=self.root_path / "backend-python", capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✅ Python unit tests passed")
                self.results["python"]["passed"] += 1
            else:
                logger.error("❌ Python unit tests failed")
                self.results["python"]["failed"] += 1
                logger.error(result.stderr)
            
            # Integration tests
            result = subprocess.run([
                "pytest", "tests/integration/", "-v", "--cov=app", "--cov-append"
            ], cwd=self.root_path / "backend-python", capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✅ Python integration tests passed")
                self.results["python"]["passed"] += 1
            else:
                logger.error("❌ Python integration tests failed")
                self.results["python"]["failed"] += 1
                logger.error(result.stderr)
            
            # Functional tests
            result = subprocess.run([
                "pytest", "tests/functional/", "-v", "--cov=app", "--cov-append"
            ], cwd=self.root_path / "backend-python", capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✅ Python functional tests passed")
                self.results["python"]["passed"] += 1
            else:
                logger.error("❌ Python functional tests failed")
                self.results["python"]["failed"] += 1
                logger.error(result.stderr)
            
            # Parse coverage
            coverage_file = self.root_path / "backend-python" / "coverage.xml"
            if coverage_file.exists():
                self.results["python"]["coverage"] = self._parse_coverage_xml(coverage_file)
            
            return self.results["python"]["failed"] == 0
            
        except Exception as e:
            logger.error(f"Error running Python tests: {e}")
            return False
    
    def run_java_tests(self) -> bool:
        """Run Java tests with coverage"""
        logger.info("☕ Running Java tests...")
        
        try:
            # Maven tests
            result = subprocess.run([
                "mvn", "clean", "test", "-Dspring.profiles.active=test"
            ], cwd=self.root_path / "backend-java", capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✅ Java tests passed")
                self.results["java"]["passed"] += 1
            else:
                logger.error("❌ Java tests failed")
                self.results["java"]["failed"] += 1
                logger.error(result.stderr)
            
            # JaCoCo coverage
            result = subprocess.run([
                "mvn", "jacoco:report"
            ], cwd=self.root_path / "backend-java", capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✅ Java coverage report generated")
                # Parse JaCoCo report
                jacoco_file = self.root_path / "backend-java" / "target" / "site" / "jacoco" / "jacoco.xml"
                if jacoco_file.exists():
                    self.results["java"]["coverage"] = self._parse_jacoco_xml(jacoco_file)
            
            return self.results["java"]["failed"] == 0
            
        except Exception as e:
            logger.error(f"Error running Java tests: {e}")
            return False
    
    def run_integration_tests(self) -> bool:
        """Run integration tests"""
        logger.info("🔗 Running integration tests...")
        
        try:
            result = subprocess.run([
                "python", "scripts/run_integration_tests.py"
            ], cwd=self.root_path, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✅ Integration tests passed")
                self.results["integration"]["passed"] += 1
            else:
                logger.error("❌ Integration tests failed")
                self.results["integration"]["failed"] += 1
                logger.error(result.stderr)
            
            return self.results["integration"]["failed"] == 0
            
        except Exception as e:
            logger.error(f"Error running integration tests: {e}")
            return False
    
    def run_e2e_tests(self) -> bool:
        """Run end-to-end tests"""
        logger.info("🌐 Running E2E tests...")
        
        try:
            result = subprocess.run([
                "pytest", "tests/e2e/", "-v", "--timeout=300"
            ], cwd=self.root_path, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✅ E2E tests passed")
                self.results["e2e"]["passed"] += 1
            else:
                logger.error("❌ E2E tests failed")
                self.results["e2e"]["failed"] += 1
                logger.error(result.stderr)
            
            return self.results["e2e"]["failed"] == 0
            
        except Exception as e:
            logger.error(f"Error running E2E tests: {e}")
            return False
    
    def run_security_tests(self) -> bool:
        """Run security tests"""
        logger.info("🔒 Running security tests...")
        
        try:
            # Security regression tests
            result = subprocess.run([
                "pytest", "tests/test_security.py", "tests/test_security_enhanced.py", "tests/test_database_security.py", "-v"
            ], cwd=self.root_path, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✅ Security tests passed")
                self.results["security"]["passed"] += 1
            else:
                logger.error("❌ Security tests failed")
                self.results["security"]["failed"] += 1
                logger.error(result.stderr)
            
            # SQL injection audit
            result = subprocess.run([
                "python", "scripts/audit_sql_injection.py"
            ], cwd=self.root_path / "backend-python", capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✅ SQL injection audit passed")
            else:
                logger.error("❌ SQL injection audit failed")
                logger.error(result.stderr)
            
            return self.results["security"]["failed"] == 0
            
        except Exception as e:
            logger.error(f"Error running security tests: {e}")
            return False
    
    def run_performance_tests(self) -> bool:
        """Run performance tests"""
        logger.info("⚡ Running performance tests...")
        
        try:
            # Check if locust is available
            result = subprocess.run(["which", "locust"], capture_output=True)
            if result.returncode != 0:
                logger.warning("⚠️ Locust not available, skipping performance tests")
                return True
            
            # Run performance tests
            result = subprocess.run([
                "locust", "-f", "tests/performance/locustfile.py", "--headless", "-u", "10", "-r", "2", "-t", "60s"
            ], cwd=self.root_path, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✅ Performance tests passed")
                self.results["performance"]["passed"] += 1
            else:
                logger.error("❌ Performance tests failed")
                self.results["performance"]["failed"] += 1
                logger.error(result.stderr)
            
            return self.results["performance"]["failed"] == 0
            
        except Exception as e:
            logger.error(f"Error running performance tests: {e}")
            return False
    
    def _parse_coverage_xml(self, coverage_file: Path) -> float:
        """Parse coverage XML file"""
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(coverage_file)
            root = tree.getroot()
            
            # Get coverage percentage
            coverage = float(root.get('line-rate', 0)) * 100
            return coverage
            
        except Exception as e:
            logger.error(f"Error parsing coverage XML: {e}")
            return 0.0
    
    def _parse_jacoco_xml(self, jacoco_file: Path) -> float:
        """Parse JaCoCo XML file"""
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(jacoco_file)
            root = tree.getroot()
            
            # Get coverage percentage
            coverage = float(root.get('line-rate', 0)) * 100
            return coverage
            
        except Exception as e:
            logger.error(f"Error parsing JaCoCo XML: {e}")
            return 0.0
    
    def generate_report(self) -> str:
        """Generate comprehensive test report"""
        report = ["🧪 Comprehensive Test Report", "=" * 50, ""]
        
        # Summary
        total_passed = sum(result["passed"] for result in self.results.values())
        total_failed = sum(result["failed"] for result in self.results.values())
        total_skipped = sum(result["skipped"] for result in self.results.values())
        
        report.append(f"📊 Summary:")
        report.append(f"  - Total passed: {total_passed}")
        report.append(f"  - Total failed: {total_failed}")
        report.append(f"  - Total skipped: {total_skipped}")
        report.append("")
        
        # Python results
        python_coverage = self.results["python"]["coverage"]
        report.append(f"🐍 Python Tests:")
        report.append(f"  - Passed: {self.results['python']['passed']}")
        report.append(f"  - Failed: {self.results['python']['failed']}")
        report.append(f"  - Coverage: {python_coverage:.1f}%")
        report.append("")
        
        # Java results
        java_coverage = self.results["java"]["coverage"]
        report.append(f"☕ Java Tests:")
        report.append(f"  - Passed: {self.results['java']['passed']}")
        report.append(f"  - Failed: {self.results['java']['failed']}")
        report.append(f"  - Coverage: {java_coverage:.1f}%")
        report.append("")
        
        # Integration results
        report.append(f"🔗 Integration Tests:")
        report.append(f"  - Passed: {self.results['integration']['passed']}")
        report.append(f"  - Failed: {self.results['integration']['failed']}")
        report.append("")
        
        # E2E results
        report.append(f"🌐 E2E Tests:")
        report.append(f"  - Passed: {self.results['e2e']['passed']}")
        report.append(f"  - Failed: {self.results['e2e']['failed']}")
        report.append("")
        
        # Security results
        report.append(f"🔒 Security Tests:")
        report.append(f"  - Passed: {self.results['security']['passed']}")
        report.append(f"  - Failed: {self.results['security']['failed']}")
        report.append("")
        
        # Performance results
        report.append(f"⚡ Performance Tests:")
        report.append(f"  - Passed: {self.results['performance']['passed']}")
        report.append(f"  - Failed: {self.results['performance']['failed']}")
        report.append("")
        
        # Overall status
        if total_failed == 0:
            report.append("✅ All tests passed!")
        else:
            report.append(f"❌ {total_failed} test suites failed!")
        
        # Coverage analysis
        avg_coverage = (python_coverage + java_coverage) / 2
        report.append("")
        report.append(f"📈 Coverage Analysis:")
        report.append(f"  - Python: {python_coverage:.1f}%")
        report.append(f"  - Java: {java_coverage:.1f}%")
        report.append(f"  - Average: {avg_coverage:.1f}%")
        
        if avg_coverage >= 80:
            report.append("  - ✅ Coverage target (80%) achieved!")
        else:
            report.append("  - ⚠️ Coverage target (80%) not achieved")
        
        return "\n".join(report)
    
    def run_all_tests(self) -> bool:
        """Run all tests"""
        logger.info("🚀 Starting comprehensive test suite...")
        
        start_time = time.time()
        
        # Run all test suites
        python_success = self.run_python_tests()
        java_success = self.run_java_tests()
        integration_success = self.run_integration_tests()
        e2e_success = self.run_e2e_tests()
        security_success = self.run_security_tests()
        performance_success = self.run_performance_tests()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Generate report
        report = self.generate_report()
        report += f"\n⏱️ Total execution time: {duration:.2f} seconds"
        
        print(report)
        
        # Save report to file
        with open("comprehensive_test_report.txt", "w") as f:
            f.write(report)
        
        logger.info("📄 Report saved to: comprehensive_test_report.txt")
        
        # Return overall success
        return all([
            python_success,
            java_success,
            integration_success,
            e2e_success,
            security_success,
            performance_success
        ])

def main():
    """Main function"""
    if len(sys.argv) > 1:
        root_path = sys.argv[1]
    else:
        root_path = "."
    
    runner = ComprehensiveTestRunner(root_path)
    success = runner.run_all_tests()
    
    if success:
        logger.info("🎉 All tests passed!")
        sys.exit(0)
    else:
        logger.error("💥 Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
