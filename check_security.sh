#!/bin/bash
# Security Check Script for TGM-Adapter
# Run this to verify no credentials are exposed

echo "🔍 Running Security Check..."
echo ""

# Check for hardcoded passwords or keys in Python files
echo "1. Checking for hardcoded credentials in .py files..."
if grep -r -n --include="*.py" -E "(password|api_key|secret|token)\s*=\s*['\"][^'\"]{10,}" . --exclude-dir=__pycache__ 2>/dev/null | grep -v "os.getenv\|os.environ\|your-.*-here\|example"; then
    echo "   ❌ FAIL: Found potential hardcoded credentials!"
else
    echo "   ✅ PASS: No hardcoded credentials found"
fi
echo ""

# Check if .env is in .gitignore
echo "2. Checking if .env is in .gitignore..."
if grep -q "^\.env$" .gitignore 2>/dev/null; then
    echo "   ✅ PASS: .env is in .gitignore"
else
    echo "   ❌ FAIL: .env is NOT in .gitignore!"
fi
echo ""

# Check if .env is tracked by git
echo "3. Checking if .env is tracked in git..."
if git ls-files | grep -q "^\.env$"; then
    echo "   ❌ FAIL: .env is still tracked in git!"
    echo "   Run: git rm --cached .env"
else
    echo "   ✅ PASS: .env is not tracked in git"
fi
echo ""

# Check if .env.example has placeholders
echo "4. Checking if .env.example has placeholders (not real credentials)..."
if grep -E "(your-.*-here|placeholder|example|XXXXX)" .env.example >/dev/null 2>&1; then
    echo "   ✅ PASS: .env.example uses placeholders"
else
    echo "   ⚠️  WARNING: .env.example might contain real credentials!"
fi
echo ""

# Check if python-dotenv is in requirements.txt
echo "5. Checking if python-dotenv is in requirements.txt..."
if grep -q "python-dotenv" requirements.txt; then
    echo "   ✅ PASS: python-dotenv is listed in requirements"
else
    echo "   ❌ FAIL: python-dotenv is missing from requirements.txt!"
fi
echo ""

# Check for AWS keys in files
echo "6. Checking for AWS access keys..."
if grep -r -n --include="*.py" --include="*.env" -E "AKIA[0-9A-Z]{16}" . 2>/dev/null | grep -v ".env.example"; then
    echo "   ❌ FAIL: Found AWS access key!"
else
    echo "   ✅ PASS: No AWS access keys found in code"
fi
echo ""

# Summary
echo "========================================="
echo "🔒 Security Check Complete!"
echo "========================================="
echo ""
echo "If all checks passed, you're good to go!"
echo "If any failed, please review SECURITY_AUDIT.md"
echo ""
