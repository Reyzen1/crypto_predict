CryptoPredict Database Export
============================
Export Date: Sat Jul 26 00:58:01 IST 2025
Source Computer: DESKTOP-M6P1TMF
Export Script: temp/export_database.sh

Contents:
---------
- postgres.tar.gz (PostgreSQL database with ALL data)
- redis.tar.gz (Redis cache data - optional)

What's Included:
---------------
✅ All database tables and data
✅ User accounts and passwords
✅ Cryptocurrency data
✅ Price history data
✅ Predictions and models
✅ Application settings
✅ Database schema and indexes

Import Instructions:
-------------------
1. Copy this entire 'database_backup' folder to target system
2. Place it in the project root directory
3. Run: ./temp/import_database.sh
4. Start application: docker-compose -f docker-compose-backend.yml up -d

File Sizes:
----------
- PostgreSQL: 1.0K
- Redis: 1.0K

Total backup size: 6.0K
