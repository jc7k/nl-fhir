#!/usr/bin/env python3
"""
File Size Enforcement Script
Enforces inviolate rule: No Python file exceeds 500 lines

Usage:
  python scripts/enforce_file_limits.py --check     # Check only
  python scripts/enforce_file_limits.py --enforce   # Block commits
  python scripts/enforce_file_limits.py --report    # Generate report
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Tuple
import subprocess

class FileSizeEnforcer:
    """Enforces maximum file size limits"""

    def __init__(self, max_lines: int = 500, src_dir: str = "src"):
        self.max_lines = max_lines
        self.src_dir = Path(src_dir)
        self.violations = []

    def check_file_sizes(self) -> List[Dict]:
        """Check all Python files for size violations"""
        violations = []

        for py_file in self.src_dir.rglob("*.py"):
            # Skip __pycache__ and test files for now
            if "__pycache__" in str(py_file):
                continue

            line_count = self._count_lines(py_file)

            if line_count > self.max_lines:
                violations.append({
                    'file': str(py_file),
                    'lines': line_count,
                    'excess': line_count - self.max_lines,
                    'severity': self._get_severity(line_count)
                })

        return violations

    def _count_lines(self, file_path: Path) -> int:
        """Count non-empty lines in file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # Count non-empty, non-comment-only lines
                meaningful_lines = [
                    line for line in lines
                    if line.strip() and not line.strip().startswith('#')
                ]
                return len(meaningful_lines)
        except Exception:
            return 0

    def _get_severity(self, line_count: int) -> str:
        """Determine violation severity"""
        if line_count > 2000:
            return "CRITICAL"
        elif line_count > 1000:
            return "HIGH"
        elif line_count > 750:
            return "MEDIUM"
        else:
            return "LOW"

    def generate_report(self) -> str:
        """Generate detailed violation report"""
        violations = self.check_file_sizes()

        if not violations:
            return "✅ All files comply with 500-line limit!"

        report = []
        report.append("🚨 FILE SIZE VIOLATIONS DETECTED")
        report.append("=" * 60)
        report.append(f"Maximum allowed lines: {self.max_lines}")
        report.append(f"Total violations: {len(violations)}")
        report.append("")

        # Sort by severity and line count
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        violations.sort(key=lambda x: (severity_order[x['severity']], -x['lines']))

        for violation in violations:
            severity_icon = {
                "CRITICAL": "🔴",
                "HIGH": "🟠",
                "MEDIUM": "🟡",
                "LOW": "🟢"
            }[violation['severity']]

            report.append(f"{severity_icon} {violation['severity']}: {violation['file']}")
            report.append(f"   Lines: {violation['lines']} (excess: +{violation['excess']})")
            report.append(f"   Refactor urgency: {self._get_refactor_urgency(violation['lines'])}")
            report.append("")

        # Recommendations
        report.append("🔧 REFACTORING RECOMMENDATIONS")
        report.append("-" * 40)

        critical_files = [v for v in violations if v['severity'] == 'CRITICAL']
        if critical_files:
            report.append("IMMEDIATE ACTION REQUIRED:")
            for violation in critical_files:
                report.append(f"  • {violation['file']} - Break into 3-5 smaller modules")

        high_files = [v for v in violations if v['severity'] == 'HIGH']
        if high_files:
            report.append("THIS SPRINT:")
            for violation in high_files:
                report.append(f"  • {violation['file']} - Extract 2-3 classes/modules")

        return "\n".join(report)

    def _get_refactor_urgency(self, line_count: int) -> str:
        """Get refactoring urgency message"""
        if line_count > 5000:
            return "🚨 IMMEDIATE - God class detected!"
        elif line_count > 2000:
            return "⚡ THIS WEEK - Major refactoring needed"
        elif line_count > 1000:
            return "📅 THIS SPRINT - Should be split"
        elif line_count > 750:
            return "🎯 NEXT SPRINT - Consider splitting"
        else:
            return "📝 Plan refactoring when touching this file"

    def enforce_pre_commit(self) -> bool:
        """Enforce limits in pre-commit hook"""
        violations = self.check_file_sizes()

        # Get files changed in this commit
        try:
            result = subprocess.run(
                ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACMR'],
                capture_output=True, text=True
            )
            changed_files = set(result.stdout.strip().split('\n'))
        except:
            changed_files = set()

        # Check if any changed files violate limits
        blocking_violations = []
        for violation in violations:
            rel_path = os.path.relpath(violation['file'])
            if rel_path in changed_files:
                blocking_violations.append(violation)

        if blocking_violations:
            print("🚫 COMMIT BLOCKED - File size violations detected!")
            print("=" * 50)
            for violation in blocking_violations:
                print(f"❌ {violation['file']}: {violation['lines']} lines (limit: {self.max_lines})")
            print("")
            print("Please refactor files to stay under the 500-line limit.")
            print("Run 'python scripts/enforce_file_limits.py --report' for details.")
            return False

        return True

    def suggest_refactoring(self, file_path: str) -> List[str]:
        """Suggest refactoring strategies for a specific file"""
        suggestions = []

        try:
            with open(file_path, 'r') as f:
                content = f.read()

            # Count classes and functions
            class_count = content.count('class ')
            function_count = content.count('def ')

            if class_count > 1:
                suggestions.append("📦 Split into separate files, one class per file")

            if function_count > 20:
                suggestions.append("🔧 Group related functions into utility modules")

            if 'Factory' in file_path and function_count > 10:
                suggestions.append("🏭 Use Factory pattern - separate factory per resource type")

            if content.count('if resource_type ==') > 5:
                suggestions.append("🎯 Replace if/elif chains with strategy pattern or registry")

            if content.count('def create_') > 10:
                suggestions.append("🎨 Extract create methods into specialized classes")

        except:
            pass

        if not suggestions:
            suggestions.append("🤔 Manual analysis needed - file is complex")

        return suggestions


def main():
    parser = argparse.ArgumentParser(description="Enforce file size limits")
    parser.add_argument('--check', action='store_true', help='Check files only')
    parser.add_argument('--enforce', action='store_true', help='Enforce in pre-commit')
    parser.add_argument('--report', action='store_true', help='Generate detailed report')
    parser.add_argument('--max-lines', type=int, default=500, help='Maximum lines per file')
    parser.add_argument('--src-dir', default='src', help='Source directory to check')

    args = parser.parse_args()

    enforcer = FileSizeEnforcer(max_lines=args.max_lines, src_dir=args.src_dir)

    if args.enforce:
        # Pre-commit hook mode
        if not enforcer.enforce_pre_commit():
            sys.exit(1)
        else:
            print("✅ All changed files comply with size limits")

    elif args.report:
        # Detailed report mode
        report = enforcer.generate_report()
        print(report)

        # Save report to file
        report_file = Path("file_size_violations.txt")
        with open(report_file, 'w') as f:
            f.write(report)
        print(f"\n📄 Report saved to: {report_file}")

    else:
        # Check mode (default)
        violations = enforcer.check_file_sizes()

        if violations:
            print(f"🚨 Found {len(violations)} file size violations:")
            for v in violations:
                print(f"  {v['severity']}: {v['file']} ({v['lines']} lines)")
            sys.exit(1)
        else:
            print("✅ All files comply with 500-line limit!")


if __name__ == "__main__":
    main()