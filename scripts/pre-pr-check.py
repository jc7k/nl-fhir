#!/usr/bin/env python3
"""
Pre-Pull Request Automated Checker
Run this script before creating a PR to catch common issues
"""

import subprocess
import sys
import re
from pathlib import Path
from typing import List, Tuple, Dict
import json

class PrePRChecker:
    """Automated pre-PR validation checks"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.issues_found = []
        self.warnings = []

    def run_command(self, cmd: List[str], check: bool = True) -> Tuple[int, str, str]:
        """Run a shell command and return results"""
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=check
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            return e.returncode, e.stdout, e.stderr

    def check_tests(self) -> bool:
        """Run test suite"""
        print("🧪 Running tests...")
        code, stdout, stderr = self.run_command(["uv", "run", "pytest", "--tb=short", "-q"])

        if code != 0:
            self.issues_found.append("❌ Tests are failing")
            # Extract failure summary
            if "failed" in stdout.lower() or "failed" in stderr.lower():
                self.issues_found.append(f"   Test output: {stderr or stdout}")
            return False

        print("   ✅ All tests passing")
        return True

    def check_linting(self) -> bool:
        """Check code style with ruff"""
        print("🎨 Checking code style...")
        code, stdout, stderr = self.run_command(["uv", "run", "ruff", "check", "src/", "tests/"], check=False)

        if code != 0:
            self.warnings.append("⚠️  Linting issues found (run: uv run ruff check --fix)")
            return False

        print("   ✅ Code style is clean")
        return True

    def check_formatting(self) -> bool:
        """Check code formatting"""
        print("📐 Checking code formatting...")
        code, stdout, stderr = self.run_command(["uv", "run", "ruff", "format", "--check", "src/", "tests/"], check=False)

        if code != 0:
            self.warnings.append("⚠️  Formatting issues found (run: uv run ruff format)")
            return False

        print("   ✅ Code formatting is correct")
        return True

    def check_common_issues(self) -> bool:
        """Check for common code review issues"""
        print("🔍 Checking for common issues...")
        issues_found = False

        # Check for common import issues
        src_files = list(Path(self.project_root / "src").rglob("*.py"))

        for file in src_files:
            content = file.read_text()

            # Check for ValidationSeverity.INFO (should be INFORMATION)
            if "ValidationSeverity.INFO" in content:
                self.issues_found.append(f"❌ {file.relative_to(self.project_root)}: Uses ValidationSeverity.INFO (should be INFORMATION)")
                issues_found = True

            # Check for unsafe high-risk medication checking
            if re.search(r'any\([^)]*in\s+medication_lower\s+for\s+[^)]*HIGH_RISK', content):
                if not re.search(r're\.escape|\\b', content):
                    self.warnings.append(f"⚠️  {file.relative_to(self.project_root)}: High-risk medication check might have false positives")

            # Check for missing re.escape in dynamic patterns
            if re.search(r'rf?["\'].*\{(?!.*re\.escape)', content):
                self.warnings.append(f"⚠️  {file.relative_to(self.project_root)}: Dynamic regex pattern might need re.escape()")

            # Check for importing from wrong modules
            if "from .clinical_validator import ValidationSeverity" in content:
                self.issues_found.append(f"❌ {file.relative_to(self.project_root)}: Imports ValidationSeverity from wrong module (use validation_common)")
                issues_found = True

        if not issues_found and not self.warnings:
            print("   ✅ No common issues found")

        return not issues_found

    def check_git_status(self) -> bool:
        """Check git repository status"""
        print("📦 Checking git status...")

        # Check for uncommitted changes
        code, stdout, _ = self.run_command(["git", "status", "--porcelain"])
        if stdout.strip():
            self.warnings.append("⚠️  Uncommitted changes found (commit or stash before PR)")

        # Check if branch is up to date with main
        self.run_command(["git", "fetch", "origin", "main"], check=False)
        code, stdout, _ = self.run_command(["git", "rev-list", "--count", "origin/main..HEAD"])

        if code == 0 and stdout.strip() == "0":
            self.warnings.append("⚠️  No commits ahead of main (did you forget to commit?)")

        # Check for merge conflicts markers
        code, stdout, _ = self.run_command(["git", "grep", "-n", "<<<<<<< "], check=False)
        if stdout:
            self.issues_found.append("❌ Merge conflict markers found in files")
            return False

        print("   ✅ Git repository is clean")
        return True

    def check_security(self) -> bool:
        """Check for security issues"""
        print("🔒 Checking security...")
        issues_found = False

        src_files = list(Path(self.project_root / "src").rglob("*.py"))

        for file in src_files:
            content = file.read_text()

            # Check for hardcoded secrets
            if re.search(r'(api_key|password|secret|token)\s*=\s*["\'][^"\']+["\']', content, re.IGNORECASE):
                # Exclude obvious non-secrets
                if not re.search(r'(api_key|password|secret|token)\s*=\s*["\'](<.*>|xxx|placeholder|your_|test)', content, re.IGNORECASE):
                    self.issues_found.append(f"❌ {file.relative_to(self.project_root)}: Possible hardcoded secret found")
                    issues_found = True

            # Check for PHI in logs
            if re.search(r'logger\.(info|debug|error).*\b(patient|ssn|dob|mrn)\b', content, re.IGNORECASE):
                self.warnings.append(f"⚠️  {file.relative_to(self.project_root)}: Might be logging PHI")

        if not issues_found:
            print("   ✅ No security issues found")

        return not issues_found

    def generate_report(self) -> int:
        """Generate final report"""
        print("\n" + "="*60)
        print("📋 PRE-PR CHECK SUMMARY")
        print("="*60)

        if not self.issues_found and not self.warnings:
            print("\n🎉 All checks passed! Ready to create PR.")
            print("\nNext steps:")
            print("1. Review your changes one more time")
            print("2. Write a clear PR description")
            print("3. Create the PR with confidence!")
            return 0

        if self.issues_found:
            print(f"\n❌ Found {len(self.issues_found)} blocking issue(s):")
            for issue in self.issues_found:
                print(f"  {issue}")

        if self.warnings:
            print(f"\n⚠️  Found {len(self.warnings)} warning(s):")
            for warning in self.warnings:
                print(f"  {warning}")

        print("\n📝 Fix these issues before creating the PR:")
        print("1. Address all ❌ blocking issues")
        print("2. Consider fixing ⚠️  warnings")
        print("3. Run this script again to verify")

        return 1 if self.issues_found else 0

    def run(self) -> int:
        """Run all checks"""
        print("🚀 Starting Pre-PR Checks...")
        print("="*60)

        # Run all checks (continue even if some fail)
        self.check_tests()
        self.check_linting()
        self.check_formatting()
        self.check_common_issues()
        self.check_security()
        self.check_git_status()

        return self.generate_report()


def main():
    """Main entry point"""
    checker = PrePRChecker()
    sys.exit(checker.run())


if __name__ == "__main__":
    main()