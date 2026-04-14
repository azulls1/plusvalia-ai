#!/bin/bash
# ================================================================
# dependency-audit.sh — Automated Dependency Vulnerability Scanner
# ================================================================
# Runs security audits on both frontend (npm) and backend (pip) deps.
#
# Usage:
#   chmod +x security/dependency-audit.sh
#   ./security/dependency-audit.sh
#
# Exit codes:
#   0 — No vulnerabilities found
#   1 — Vulnerabilities found or audit tool missing
# ================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root (relative to this script's location)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

AUDIT_REPORT="$SCRIPT_DIR/audit-report-$(date +%Y%m%d-%H%M%S).txt"
EXIT_CODE=0

echo -e "${BLUE}================================================================${NC}"
echo -e "${BLUE}  Security Dependency Audit — $(date)${NC}"
echo -e "${BLUE}================================================================${NC}"
echo ""

# Write header to report file
{
  echo "Security Dependency Audit Report"
  echo "Date: $(date)"
  echo "Project: $PROJECT_ROOT"
  echo "================================"
  echo ""
} > "$AUDIT_REPORT"

# ==================== Frontend Audit (npm) ====================

echo -e "${YELLOW}=== Frontend Audit (npm) ===${NC}"
echo ""

FRONTEND_DIR="$PROJECT_ROOT/app"

if [ -d "$FRONTEND_DIR" ] && [ -f "$FRONTEND_DIR/package.json" ]; then
  cd "$FRONTEND_DIR"

  if command -v npm &> /dev/null; then
    echo "Running npm audit on $FRONTEND_DIR..."
    echo ""

    # Run audit and capture output
    if npm audit --production 2>&1 | tee -a "$AUDIT_REPORT"; then
      echo -e "${GREEN}[PASS] No npm vulnerabilities found.${NC}"
    else
      echo -e "${RED}[WARN] npm vulnerabilities detected. Review output above.${NC}"
      EXIT_CODE=1
    fi
  else
    echo -e "${RED}[ERROR] npm not found. Install Node.js to run frontend audit.${NC}"
    EXIT_CODE=1
  fi
else
  echo -e "${YELLOW}[SKIP] Frontend directory not found at $FRONTEND_DIR${NC}"
fi

echo ""

# ==================== Backend Audit (pip-audit) ====================

echo -e "${YELLOW}=== Backend Audit (pip-audit) ===${NC}"
echo ""

BACKEND_DIR="$PROJECT_ROOT/python_services"

if [ -d "$BACKEND_DIR" ]; then
  cd "$BACKEND_DIR"

  if [ -f "requirements.txt" ]; then
    if command -v pip-audit &> /dev/null; then
      echo "Running pip-audit on $BACKEND_DIR/requirements.txt..."
      echo ""

      if pip-audit -r requirements.txt 2>&1 | tee -a "$AUDIT_REPORT"; then
        echo -e "${GREEN}[PASS] No pip vulnerabilities found.${NC}"
      else
        echo -e "${RED}[WARN] pip vulnerabilities detected. Review output above.${NC}"
        EXIT_CODE=1
      fi
    else
      echo -e "${YELLOW}[INFO] pip-audit not installed. Installing...${NC}"
      pip install pip-audit 2>/dev/null

      if command -v pip-audit &> /dev/null; then
        if pip-audit -r requirements.txt 2>&1 | tee -a "$AUDIT_REPORT"; then
          echo -e "${GREEN}[PASS] No pip vulnerabilities found.${NC}"
        else
          echo -e "${RED}[WARN] pip vulnerabilities detected.${NC}"
          EXIT_CODE=1
        fi
      else
        echo -e "${RED}[ERROR] Could not install pip-audit. Run: pip install pip-audit${NC}"
        EXIT_CODE=1
      fi
    fi
  else
    echo -e "${YELLOW}[SKIP] requirements.txt not found in $BACKEND_DIR${NC}"
  fi
else
  echo -e "${YELLOW}[SKIP] Backend directory not found at $BACKEND_DIR${NC}"
fi

echo ""

# ==================== Secret Scanning ====================

echo -e "${YELLOW}=== Secret Scanning ===${NC}"
echo ""

cd "$PROJECT_ROOT"

echo "Checking for potential secrets in tracked files..."
echo ""

# Patterns to search for (simplified grep-based secret scanning)
SECRET_FOUND=false

# Check for hardcoded JWT tokens (long base64 strings with dots)
if grep -rn "eyJ[a-zA-Z0-9_-]\{20,\}\." --include="*.ts" --include="*.js" --include="*.py" --include="*.json" \
   --exclude-dir=node_modules --exclude-dir=.angular --exclude-dir=__pycache__ \
   --exclude="*.env.example" "$PROJECT_ROOT" 2>/dev/null; then
  echo -e "${RED}[WARN] Potential JWT tokens found in source files!${NC}"
  SECRET_FOUND=true
fi

# Check for password patterns
if grep -rni "password\s*=\s*['\"][^'\"]\{4,\}['\"]" --include="*.ts" --include="*.js" --include="*.py" \
   --exclude-dir=node_modules --exclude-dir=.angular --exclude-dir=__pycache__ \
   --exclude="*.env.example" --exclude="*.env" "$PROJECT_ROOT" 2>/dev/null; then
  echo -e "${RED}[WARN] Potential hardcoded passwords found!${NC}"
  SECRET_FOUND=true
fi

if [ "$SECRET_FOUND" = false ]; then
  echo -e "${GREEN}[PASS] No obvious secrets found in source files.${NC}"
fi

echo ""

# ==================== .gitignore Verification ====================

echo -e "${YELLOW}=== .gitignore Verification ===${NC}"
echo ""

REQUIRED_PATTERNS=(".env" "*.pem" "*.key" "*.cert" "*.pkl" "credentials*.json")

if [ -f "$PROJECT_ROOT/.gitignore" ]; then
  for pattern in "${REQUIRED_PATTERNS[@]}"; do
    if grep -qF "$pattern" "$PROJECT_ROOT/.gitignore" 2>/dev/null; then
      echo -e "${GREEN}  [OK] '$pattern' is in .gitignore${NC}"
    else
      echo -e "${RED}  [MISSING] '$pattern' is NOT in .gitignore${NC}"
      EXIT_CODE=1
    fi
  done
else
  echo -e "${RED}[ERROR] No .gitignore found at project root!${NC}"
  EXIT_CODE=1
fi

echo ""

# ==================== Summary ====================

echo -e "${BLUE}================================================================${NC}"
if [ $EXIT_CODE -eq 0 ]; then
  echo -e "${GREEN}  AUDIT PASSED — No critical issues found.${NC}"
else
  echo -e "${RED}  AUDIT FOUND ISSUES — Review warnings above.${NC}"
fi
echo -e "${BLUE}  Full report saved to: $AUDIT_REPORT${NC}"
echo -e "${BLUE}================================================================${NC}"

exit $EXIT_CODE
