#!/usr/bin/env python3
"""
Integration Test Runner for Java-Python Communication
This script runs comprehensive integration tests between Java and Python backends
"""

import os
import sys
import time
import requests
import subprocess
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ServiceStatus(Enum):
    """Service status enumeration"""
    UNKNOWN = "unknown"
    STARTING = "starting"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    STOPPED = "stopped"

@dataclass
class ServiceInfo:
    """Service information"""
    name: str
    url: str
    port: int
    status: ServiceStatus = ServiceStatus.UNKNOWN
    health_endpoint: str = "/health"
    startup_time: float = 0.0
    last_check: float = 0.0

class IntegrationTestRunner:
    """Integration test runner for Java-Python communication"""
    
    def __init__(self):
        self.services = {
            "java": ServiceInfo(
                name="Java Backend",
                url="http://localhost:8080",
                port=8080,
                health_endpoint="/api/health"
            ),
            "python": ServiceInfo(
                name="Python Backend",
                url="http://localhost:8000",
                port=8000,
                health_endpoint="/java/health"
            )
        }
        self.test_results = []
        self.start_time = time.time()
        
    def check_service_health(self, service_name: str) -> bool:
        """Check if a service is healthy"""
        service = self.services[service_name]
        try:
            response = requests.get(
                f"{service.url}{service.health_endpoint}",
                timeout=5
            )
            service.status = ServiceStatus.HEALTHY if response.status_code == 200 else ServiceStatus.UNHEALTHY
            service.last_check = time.time()
            return service.status == ServiceStatus.HEALTHY
        except requests.exceptions.RequestException as e:
            logger.warning(f"Health check failed for {service_name}: {e}")
            service.status = ServiceStatus.UNHEALTHY
            service.last_check = time.time()
            return False
    
    def wait_for_services(self, timeout: int = 60) -> bool:
        """Wait for all services to be healthy"""
        logger.info("Waiting for services to be healthy...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            all_healthy = True
            for service_name in self.services:
                if not self.check_service_health(service_name):
                    all_healthy = False
                    logger.info(f"Waiting for {service_name} to be healthy...")
                    time.sleep(2)
                    break
            
            if all_healthy:
                logger.info("All services are healthy!")
                return True
        
        logger.error("Timeout waiting for services to be healthy")
        return False
    
    def run_java_tests(self) -> bool:
        """Run Java integration tests"""
        logger.info("Running Java integration tests...")
        try:
            # Change to Java backend directory
            java_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend-java")
            os.chdir(java_dir)
            
            # Run Maven tests
            result = subprocess.run(
                ["mvn", "test", "-Dtest=JavaPythonIntegrationTest"],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                logger.info("Java integration tests passed")
                return True
            else:
                logger.error(f"Java integration tests failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Java integration tests timed out")
            return False
        except Exception as e:
            logger.error(f"Error running Java integration tests: {e}")
            return False
    
    def run_python_tests(self) -> bool:
        """Run Python integration tests"""
        logger.info("Running Python integration tests...")
        try:
            # Change to project root
            project_root = os.path.dirname(os.path.dirname(__file__))
            os.chdir(project_root)
            
            # Run Python tests
            result = subprocess.run(
                ["python", "-m", "pytest", "tests/integration/test_java_python_integration.py", "-v"],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                logger.info("Python integration tests passed")
                return True
            else:
                logger.error(f"Python integration tests failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Python integration tests timed out")
            return False
        except Exception as e:
            logger.error(f"Error running Python integration tests: {e}")
            return False
    
    def test_java_python_communication(self) -> bool:
        """Test direct Java-Python communication"""
        logger.info("Testing Java-Python communication...")
        
        test_cases = [
            {
                "name": "Text Analysis",
                "url": f"{self.services['java'].url}/api/analysis/analyze-product",
                "method": "POST",
                "data": {
                    "text": "Aqua, Glycerin, Hyaluronic Acid, Niacinamide",
                    "user_need": "sensitive skin"
                }
            },
            {
                "name": "Health Check",
                "url": f"{self.services['java'].url}/api/health",
                "method": "GET",
                "data": None
            },
            {
                "name": "Substitution Analysis",
                "url": f"{self.services['java'].url}/api/substitution/alternatives",
                "method": "POST",
                "data": {
                    "problematic_ingredients": ["Sodium Lauryl Sulfate", "Parabens"],
                    "user_conditions": ["sensitive skin", "eczema"]
                }
            }
        ]
        
        success_count = 0
        for test_case in test_cases:
            try:
                if test_case["method"] == "GET":
                    response = requests.get(test_case["url"], timeout=10)
                else:
                    response = requests.post(
                        test_case["url"],
                        json=test_case["data"],
                        timeout=10
                    )
                
                if response.status_code == 200:
                    logger.info(f"✓ {test_case['name']} test passed")
                    success_count += 1
                else:
                    logger.error(f"✗ {test_case['name']} test failed: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"✗ {test_case['name']} test failed: {e}")
        
        success_rate = success_count / len(test_cases)
        logger.info(f"Java-Python communication tests: {success_count}/{len(test_cases)} passed ({success_rate:.1%})")
        return success_rate >= 0.8
    
    def test_python_services(self) -> bool:
        """Test Python backend services"""
        logger.info("Testing Python backend services...")
        
        test_cases = [
            {
                "name": "Python Health",
                "url": f"{self.services['python'].url}/java/health",
                "method": "GET"
            },
            {
                "name": "Ollama Status",
                "url": f"{self.services['python'].url}/ollama/status",
                "method": "GET"
            },
            {
                "name": "Direct Text Analysis",
                "url": f"{self.services['python'].url}/java/analyze-text",
                "method": "POST",
                "data": {
                    "text": "Aqua, Glycerin, Hyaluronic Acid",
                    "user_need": "general safety"
                }
            }
        ]
        
        success_count = 0
        for test_case in test_cases:
            try:
                if test_case["method"] == "GET":
                    response = requests.get(test_case["url"], timeout=10)
                else:
                    response = requests.post(
                        test_case["url"],
                        data=test_case["data"],
                        timeout=10
                    )
                
                if response.status_code == 200:
                    logger.info(f"✓ {test_case['name']} test passed")
                    success_count += 1
                else:
                    logger.error(f"✗ {test_case['name']} test failed: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"✗ {test_case['name']} test failed: {e}")
        
        success_rate = success_count / len(test_cases)
        logger.info(f"Python services tests: {success_count}/{len(test_cases)} passed ({success_rate:.1%})")
        return success_rate >= 0.8
    
    def run_performance_tests(self) -> bool:
        """Run performance tests"""
        logger.info("Running performance tests...")
        
        # Test concurrent requests
        import concurrent.futures
        import threading
        
        def make_request():
            try:
                response = requests.post(
                    f"{self.services['java'].url}/api/analysis/analyze-product",
                    json={
                        "text": "Aqua, Glycerin, Hyaluronic Acid, Niacinamide",
                        "user_need": "sensitive skin"
                    },
                    timeout=30
                )
                return response.status_code == 200
            except:
                return False
        
        # Test with 5 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            results = [future.result() for future in futures]
        
        success_count = sum(results)
        success_rate = success_count / len(results)
        
        logger.info(f"Performance tests: {success_count}/{len(results)} concurrent requests succeeded ({success_rate:.1%})")
        return success_rate >= 0.8
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate integration test report"""
        end_time = time.time()
        total_time = end_time - self.start_time
        
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_time": total_time,
            "services": {},
            "test_results": self.test_results,
            "summary": {
                "total_tests": len(self.test_results),
                "passed": sum(1 for result in self.test_results if result.get("passed", False)),
                "failed": sum(1 for result in self.test_results if not result.get("passed", False))
            }
        }
        
        for service_name, service in self.services.items():
            report["services"][service_name] = {
                "name": service.name,
                "url": service.url,
                "status": service.status.value,
                "last_check": service.last_check
            }
        
        return report
    
    def run_all_tests(self) -> bool:
        """Run all integration tests"""
        logger.info("Starting integration test suite...")
        
        # Wait for services to be healthy
        if not self.wait_for_services():
            logger.error("Services are not healthy, aborting tests")
            return False
        
        # Run tests
        tests = [
            ("Java-Python Communication", self.test_java_python_communication),
            ("Python Services", self.test_python_services),
            ("Performance Tests", self.run_performance_tests),
            ("Java Integration Tests", self.run_java_tests),
            ("Python Integration Tests", self.run_python_tests)
        ]
        
        all_passed = True
        for test_name, test_func in tests:
            logger.info(f"Running {test_name}...")
            try:
                result = test_func()
                self.test_results.append({
                    "name": test_name,
                    "passed": result,
                    "timestamp": time.time()
                })
                if not result:
                    all_passed = False
            except Exception as e:
                logger.error(f"Error running {test_name}: {e}")
                self.test_results.append({
                    "name": test_name,
                    "passed": False,
                    "error": str(e),
                    "timestamp": time.time()
                })
                all_passed = False
        
        # Generate report
        report = self.generate_report()
        
        # Print summary
        logger.info("=" * 50)
        logger.info("INTEGRATION TEST SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Total time: {report['total_time']:.2f} seconds")
        logger.info(f"Tests passed: {report['summary']['passed']}/{report['summary']['total_tests']}")
        logger.info(f"Tests failed: {report['summary']['failed']}/{report['summary']['total_tests']}")
        
        for result in self.test_results:
            status = "✓ PASSED" if result.get("passed", False) else "✗ FAILED"
            logger.info(f"{status}: {result['name']}")
        
        return all_passed

def main():
    """Main function"""
    runner = IntegrationTestRunner()
    success = runner.run_all_tests()
    
    if success:
        logger.info("All integration tests passed!")
        sys.exit(0)
    else:
        logger.error("Some integration tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
