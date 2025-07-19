#!/bin/bash
# File: scripts/fix-models.sh
# Fix models file import issue

set -e

echo "🔧 Fixing Models Import Issue"
echo "============================="

# Check if models file exists
if [ ! -f "backend/app/models/__init__.py" ]; then
    echo "❌ Models file not found. Creating new one..."
    chmod +x scripts/create-models.sh
    ./scripts/create-models.sh
    exit 0
fi

# Fix the import in existing file
echo "🔧 Fixing import statements..."
sed -i 's/from sqlalchemy import Column, Integer, String, Boolean, DateTime, Decimal, ForeignKey, Text, Index/from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Index/' backend/app/models/__init__.py

# Add correct import for Numeric
sed -i '/from sqlalchemy import/a from sqlalchemy.sql.sqltypes import Numeric' backend/app/models/__init__.py

# Replace all Decimal with Numeric
sed -i 's/Decimal(/Numeric(/g' backend/app/models/__init__.py

echo "✅ Models file fixed successfully!"
echo ""
echo "Fixed issues:"
echo "  - Removed Decimal from sqlalchemy import"
echo "  - Added Numeric import from sqlalchemy.sql.sqltypes"
echo "  - Replaced all Decimal() with Numeric()"
echo ""
echo "Next: Run ./scripts/setup-db.sh"