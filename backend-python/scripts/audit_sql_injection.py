#!/usr/bin/env python3
"""
SQL Injection Audit Script
Scans codebase for potential SQL injection vulnerabilities
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Any
import ast
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SQLInjectionAuditor:
    """Audit codebase for SQL injection vulnerabilities"""
    
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.vulnerabilities = []
        self.safe_patterns = [
            r'SELECT\s+\*\s+FROM\s+\w+',  # Simple SELECT *
            r'INSERT\s+INTO\s+\w+\s+VALUES',  # Simple INSERT
            r'UPDATE\s+\w+\s+SET\s+\w+\s*=',  # Simple UPDATE
            r'DELETE\s+FROM\s+\w+',  # Simple DELETE
        ]
    
    def scan_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Scan a single file for SQL injection vulnerabilities"""
        vulnerabilities = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for raw SQL queries
            sql_patterns = [
                r'execute\s*\(\s*["\'].*["\']',  # execute() with string
                r'query\s*\(\s*["\'].*["\']',   # query() with string
                r'raw\s*\(\s*["\'].*["\']',    # raw() with string
                r'text\s*\(\s*["\'].*["\']',   # text() with string
            ]
            
            for pattern in sql_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    
                    # Check if it's a safe pattern
                    if not self._is_safe_pattern(match.group()):
                        vulnerabilities.append({
                            'file': str(file_path),
                            'line': line_num,
                            'type': 'potential_sql_injection',
                            'severity': 'high',
                            'description': 'Raw SQL query detected',
                            'code': match.group().strip(),
                            'recommendation': 'Use parameterized queries or ORM methods'
                        })
            
            # Look for string formatting in SQL
            format_patterns = [
                r'["\'].*%s.*["\']',  # %s formatting
                r'["\'].*{.*}.*["\']',  # {} formatting
                r'["\'].*\+.*["\']',   # String concatenation
            ]
            
            for pattern in format_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    
                    # Check if it's in a SQL context
                    if self._is_sql_context(content, match.start()):
                        vulnerabilities.append({
                            'file': str(file_path),
                            'line': line_num,
                            'type': 'string_formatting_in_sql',
                            'severity': 'high',
                            'description': 'String formatting in SQL query',
                            'code': match.group().strip(),
                            'recommendation': 'Use parameterized queries'
                        })
            
            # Look for f-strings in SQL
            f_string_pattern = r'f["\'].*{.*}.*["\']'
            matches = re.finditer(f_string_pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                
                if self._is_sql_context(content, match.start()):
                    vulnerabilities.append({
                        'file': str(file_path),
                        'line': line_num,
                        'type': 'f_string_in_sql',
                        'severity': 'high',
                        'description': 'F-string in SQL query',
                        'code': match.group().strip(),
                        'recommendation': 'Use parameterized queries'
                    })
        
        except Exception as e:
            logger.error(f"Error scanning {file_path}: {e}")
        
        return vulnerabilities
    
    def _is_safe_pattern(self, code: str) -> bool:
        """Check if the SQL pattern is safe"""
        for pattern in self.safe_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                return True
        return False
    
    def _is_sql_context(self, content: str, position: int) -> bool:
        """Check if the position is in a SQL context"""
        # Look for SQL keywords before the position
        sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'FROM', 'WHERE', 'JOIN']
        
        # Get the line containing the position
        lines = content[:position].split('\n')
        current_line = lines[-1] if lines else ""
        
        for keyword in sql_keywords:
            if keyword.lower() in current_line.lower():
                return True
        
        return False
    
    def scan_directory(self) -> List[Dict[str, Any]]:
        """Scan entire directory for SQL injection vulnerabilities"""
        all_vulnerabilities = []
        
        # Scan Python files
        for py_file in self.root_path.rglob("*.py"):
            if 'migrations' in str(py_file) or 'venv' in str(py_file):
                continue
            
            vulnerabilities = self.scan_file(py_file)
            all_vulnerabilities.extend(vulnerabilities)
        
        return all_vulnerabilities
    
    def generate_report(self, vulnerabilities: List[Dict[str, Any]]) -> str:
        """Generate a security report"""
        if not vulnerabilities:
            return "✅ No SQL injection vulnerabilities found!"
        
        report = ["🔍 SQL Injection Security Audit Report", "=" * 50, ""]
        
        # Group by severity
        high_severity = [v for v in vulnerabilities if v['severity'] == 'high']
        medium_severity = [v for v in vulnerabilities if v['severity'] == 'medium']
        low_severity = [v for v in vulnerabilities if v['severity'] == 'low']
        
        report.append(f"📊 Summary:")
        report.append(f"  - High severity: {len(high_severity)}")
        report.append(f"  - Medium severity: {len(medium_severity)}")
        report.append(f"  - Low severity: {len(low_severity)}")
        report.append("")
        
        # High severity issues
        if high_severity:
            report.append("🚨 HIGH SEVERITY ISSUES:")
            report.append("-" * 30)
            for vuln in high_severity:
                report.append(f"File: {vuln['file']}")
                report.append(f"Line: {vuln['line']}")
                report.append(f"Type: {vuln['type']}")
                report.append(f"Description: {vuln['description']}")
                report.append(f"Code: {vuln['code']}")
                report.append(f"Recommendation: {vuln['recommendation']}")
                report.append("")
        
        return "\n".join(report)

def main():
    """Main function"""
    if len(sys.argv) > 1:
        root_path = sys.argv[1]
    else:
        root_path = "."
    
    auditor = SQLInjectionAuditor(root_path)
    vulnerabilities = auditor.scan_directory()
    
    report = auditor.generate_report(vulnerabilities)
    print(report)
    
    # Save report to file
    with open("sql_injection_audit_report.txt", "w") as f:
        f.write(report)
    
    print(f"\n📄 Report saved to: sql_injection_audit_report.txt")
    
    # Exit with error code if high severity issues found
    high_severity_count = len([v for v in vulnerabilities if v['severity'] == 'high'])
    if high_severity_count > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
