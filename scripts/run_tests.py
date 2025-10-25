#!/usr/bin/env python3
"""
Comprehensive Test Runner for MommyShops Project
Runs unit, integration, and E2E tests with coverage reporting
"""

import os
import sys
import subprocess
import argparse
import time
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestType(Enum):
    """Test type enumeration"""
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    ALL = "all"

class TestResult(Enum):
    """Test result enumeration"""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"

@dataclass
class TestConfig:
    """Test configuration"""
    test_type: TestType
    coverage_threshold: float = 80.0
    parallel_workers: int = 4
    timeout: int = 300
    verbose: bool = True
    html_report: bool = True
    json_report: bool = True
    benchmark: bool = False
    security_scan: bool = False
    performance_test: bool = False

@dataclass
class TestResult:
    """Test result data"""
    test_name: str
    result: TestResult
    duration: float
    coverage: float
    errors: List[str]
    warnings: List[str]

class TestRunner:
    """Comprehensive test runner for MommyShops project"""
    
    def __init__(self, config: TestConfig):
        self.config = config
        self.results: List[TestResult] = []
        self.start_time = time.time()
        
    def run_python_tests(self) -> bool:
        """Run Python tests"""
        print("🐍 Running Python tests...")
        
        # Change to project root
        project_root = os.path.dirname(os.path.dirname(__file__))
        os.chdir(project_root)
        
        # Build pytest command
        cmd = ["python", "-m", "pytest"]
        
        # Add test paths based on type
        if self.config.test_type == TestType.UNIT:
            cmd.extend(["tests/unit/", "-m", "unit"])
        elif self.config.test_type == TestType.INTEGRATION:
            cmd.extend(["tests/integration/", "-m", "integration"])
        elif self.config.test_type == TestType.E2E:
            cmd.extend(["tests/e2e/", "-m", "e2e"])
        else:  # ALL
            cmd.extend(["tests/"])
        
        # Add options
        cmd.extend([
            "-v" if self.config.verbose else "",
            f"--cov=backend-python",
            f"--cov-fail-under={self.config.coverage_threshold}",
            f"--cov-report=html:htmlcov" if self.config.html_report else "",
            f"--cov-report=json:coverage.json" if self.config.json_report else "",
            f"--cov-report=term-missing",
            f"-n{self.config.parallel_workers}" if self.config.parallel_workers > 1 else "",
            f"--timeout={self.config.timeout}",
            "--tb=short",
            "--strict-markers",
            "--disable-warnings"
        ])
        
        # Remove empty strings
        cmd = [arg for arg in cmd if arg]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.config.timeout)
            
            if result.returncode == 0:
                print("✅ Python tests passed")
                return True
            else:
                print(f"❌ Python tests failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("⏰ Python tests timed out")
            return False
        except Exception as e:
            print(f"💥 Error running Python tests: {e}")
            return False
    
    def run_java_tests(self) -> bool:
        """Run Java tests"""
        print("☕ Running Java tests...")
        
        # Change to Java backend directory
        java_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend-java")
        os.chdir(java_dir)
        
        try:
            # Run Maven tests
            cmd = ["mvn", "test", "-Dtest=*Test", "-DfailIfNoTests=false"]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.config.timeout)
            
            if result.returncode == 0:
                print("✅ Java tests passed")
                return True
            else:
                print(f"❌ Java tests failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("⏰ Java tests timed out")
            return False
        except Exception as e:
            print(f"💥 Error running Java tests: {e}")
            return False
    
    def run_integration_tests(self) -> bool:
        """Run integration tests"""
        print("🔗 Running integration tests...")
        
        # Run the integration test script
        integration_script = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            "scripts", 
            "run_integration_tests.py"
        )
        
        try:
            result = subprocess.run(
                ["python", integration_script],
                capture_output=True,
                text=True,
                timeout=self.config.timeout
            )
            
            if result.returncode == 0:
                print("✅ Integration tests passed")
                return True
            else:
                print(f"❌ Integration tests failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("⏰ Integration tests timed out")
            return False
        except Exception as e:
            print(f"💥 Error running integration tests: {e}")
            return False
    
    def run_security_scan(self) -> bool:
        """Run security scan"""
        print("🔒 Running security scan...")
        
        # Change to project root
        project_root = os.path.dirname(os.path.dirname(__file__))
        os.chdir(project_root)
        
        try:
            # Run bandit security scan
            cmd = ["bandit", "-r", "backend-python/", "-f", "json", "-o", "security-report.json"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print("✅ Security scan passed")
                return True
            else:
                print(f"⚠️ Security issues found: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("⏰ Security scan timed out")
            return False
        except Exception as e:
            print(f"💥 Error running security scan: {e}")
            return False
    
    def run_performance_tests(self) -> bool:
        """Run performance tests"""
        print("⚡ Running performance tests...")
        
        # Change to project root
        project_root = os.path.dirname(os.path.dirname(__file__))
        os.chdir(project_root)
        
        try:
            # Run performance tests with pytest-benchmark
            cmd = [
                "python", "-m", "pytest", 
                "tests/", "-m", "benchmark",
                "--benchmark-only",
                "--benchmark-save=performance-report"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.config.timeout)
            
            if result.returncode == 0:
                print("✅ Performance tests passed")
                return True
            else:
                print(f"❌ Performance tests failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("⏰ Performance tests timed out")
            return False
        except Exception as e:
            print(f"💥 Error running performance tests: {e}")
            return False
    
    def run_all_tests(self) -> bool:
        """Run all tests based on configuration"""
        print("🚀 Starting comprehensive test suite...")
        print(f"📊 Test type: {self.config.test_type.value}")
        print(f"📈 Coverage threshold: {self.config.coverage_threshold}%")
        print(f"👥 Parallel workers: {self.config.parallel_workers}")
        print(f"⏱️ Timeout: {self.config.timeout}s")
        print("=" * 50)
        
        all_passed = True
        
        # Run Python tests
        if self.config.test_type in [TestType.UNIT, TestType.ALL]:
            if not self.run_python_tests():
                all_passed = False
        
        # Run Java tests
        if self.config.test_type in [TestType.UNIT, TestType.ALL]:
            if not self.run_java_tests():
                all_passed = False
        
        # Run integration tests
        if self.config.test_type in [TestType.INTEGRATION, TestType.ALL]:
            if not self.run_integration_tests():
                all_passed = False
        
        # Run E2E tests
        if self.config.test_type in [TestType.E2E, TestType.ALL]:
            if not self.run_integration_tests():  # E2E tests are part of integration
                all_passed = False
        
        # Run security scan
        if self.config.security_scan:
            if not self.run_security_scan():
                all_passed = False
        
        # Run performance tests
        if self.config.performance_test:
            if not self.run_performance_tests():
                all_passed = False
        
        # Generate report
        self.generate_report()
        
        return all_passed
    
    def generate_report(self):
        """Generate test report"""
        end_time = time.time()
        total_time = end_time - self.start_time
        
        print("=" * 50)
        print("📊 TEST REPORT")
        print("=" * 50)
        print(f"⏱️ Total time: {total_time:.2f} seconds")
        print(f"📈 Test type: {self.config.test_type.value}")
        print(f"🎯 Coverage threshold: {self.config.coverage_threshold}%")
        print(f"👥 Parallel workers: {self.config.parallel_workers}")
        print(f"⏱️ Timeout: {self.config.timeout}s")
        
        # Check for coverage report
        if os.path.exists("htmlcov/index.html"):
            print("📊 Coverage report: htmlcov/index.html")
        
        if os.path.exists("coverage.json"):
            print("📊 Coverage JSON: coverage.json")
        
        if os.path.exists("security-report.json"):
            print("🔒 Security report: security-report.json")
        
        if os.path.exists("performance-report.json"):
            print("⚡ Performance report: performance-report.json")
        
        print("=" * 50)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Run MommyShops tests")
    parser.add_argument("--type", choices=["unit", "integration", "e2e", "all"], 
                       default="all", help="Test type to run")
    parser.add_argument("--coverage", type=float, default=80.0, 
                       help="Coverage threshold percentage")
    parser.add_argument("--workers", type=int, default=4, 
                       help="Number of parallel workers")
    parser.add_argument("--timeout", type=int, default=300, 
                       help="Test timeout in seconds")
    parser.add_argument("--verbose", action="store_true", 
                       help="Verbose output")
    parser.add_argument("--no-html", action="store_true", 
                       help="Disable HTML report")
    parser.add_argument("--no-json", action="store_true", 
                       help="Disable JSON report")
    parser.add_argument("--benchmark", action="store_true", 
                       help="Run performance benchmarks")
    parser.add_argument("--security", action="store_true", 
                       help="Run security scan")
    parser.add_argument("--performance", action="store_true", 
                       help="Run performance tests")
    
    args = parser.parse_args()
    
    # Create configuration
    config = TestConfig(
        test_type=TestType(args.type),
        coverage_threshold=args.coverage,
        parallel_workers=args.workers,
        timeout=args.timeout,
        verbose=args.verbose,
        html_report=not args.no_html,
        json_report=not args.no_json,
        benchmark=args.benchmark,
        security_scan=args.security,
        performance_test=args.performance
    )
    
    # Run tests
    runner = TestRunner(config)
    success = runner.run_all_tests()
    
    if success:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("💥 Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
