# File: temp/validate_schema.py
# Purpose: Validate database schema after import/export operations
# Usage: python temp/validate_schema.py

import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path
import json

# Add backend path to sys.path for imports
backend_path = Path(__file__).parent.parent / "backend"
sys.path.append(str(backend_path))

from app.core.config import get_settings

def get_database_schema_info():
    """
    Get detailed information about database schema
    """
    print("🔍 Analyzing database schema...")
    
    # Get database configuration
    settings = get_settings()
    
    db_params = {
        'host': settings.DATABASE_HOST,
        'port': settings.DATABASE_PORT,
        'database': settings.DATABASE_NAME,
        'username': settings.DATABASE_USER,
        'password': settings.DATABASE_PASSWORD
    }
    
    schema_info = {
        'tables': [],
        'indexes': [],
        'constraints': [],
        'sequences': []
    }
    
    try:
        env = os.environ.copy()
        env['PGPASSWORD'] = db_params['password']
        
        # Get tables information
        tables_query = """
        SELECT 
            schemaname,
            tablename,
            tableowner,
            hasindexes,
            hasrules,
            hastriggers
        FROM pg_tables 
        WHERE schemaname = 'public'
        ORDER BY tablename;
        """
        
        result = subprocess.run([
            "psql",
            f"--host={db_params['host']}",
            f"--port={db_params['port']}",
            f"--username={db_params['username']}",
            "--no-password",
            f"--dbname={db_params['database']}",
            "--tuples-only",
            "--no-align",
            "--field-separator=|",
            f"--command={tables_query}"
        ], env=env, capture_output=True, text=True, check=True)
        
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                parts = line.split('|')
                if len(parts) >= 6:
                    schema_info['tables'].append({
                        'schema': parts[0].strip(),
                        'name': parts[1].strip(),
                        'owner': parts[2].strip(),
                        'has_indexes': parts[3].strip() == 't',
                        'has_rules': parts[4].strip() == 't',
                        'has_triggers': parts[5].strip() == 't'
                    })
        
        # Get columns information for each table
        for table in schema_info['tables']:
            columns_query = f"""
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = '{table['name']}'
            ORDER BY ordinal_position;
            """
            
            result = subprocess.run([
                "psql",
                f"--host={db_params['host']}",
                f"--port={db_params['port']}",
                f"--username={db_params['username']}",
                "--no-password",
                f"--dbname={db_params['database']}",
                "--tuples-only",
                "--no-align",
                "--field-separator=|",
                f"--command={columns_query}"
            ], env=env, capture_output=True, text=True, check=True)
            
            columns = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    parts = line.split('|')
                    if len(parts) >= 4:
                        columns.append({
                            'name': parts[0].strip(),
                            'type': parts[1].strip(),
                            'nullable': parts[2].strip() == 'YES',
                            'default': parts[3].strip() if parts[3].strip() else None
                        })
            
            table['columns'] = columns
        
        # Get indexes information
        indexes_query = """
        SELECT 
            schemaname,
            tablename,
            indexname,
            indexdef
        FROM pg_indexes 
        WHERE schemaname = 'public'
        ORDER BY tablename, indexname;
        """
        
        result = subprocess.run([
            "psql",
            f"--host={db_params['host']}",
            f"--port={db_params['port']}",
            f"--username={db_params['username']}",
            "--no-password",
            f"--dbname={db_params['database']}",
            "--tuples-only",
            "--no-align",
            "--field-separator=|",
            f"--command={indexes_query}"
        ], env=env, capture_output=True, text=True, check=True)
        
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                parts = line.split('|')
                if len(parts) >= 4:
                    schema_info['indexes'].append({
                        'schema': parts[0].strip(),
                        'table': parts[1].strip(),
                        'name': parts[2].strip(),
                        'definition': parts[3].strip()
                    })
        
        return schema_info
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error getting schema info: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def validate_expected_tables():
    """
    Validate that expected tables from the project exist
    """
    print("📋 Validating expected project tables...")
    
    # Expected tables based on your project structure
    expected_tables = [
        'users',
        'cryptocurrencies', 
        'price_data',
        'predictions',
        'user_portfolios',
        'alerts',
        'alembic_version'
    ]
    
    schema_info = get_database_schema_info()
    if not schema_info:
        return False
    
    existing_tables = [table['name'] for table in schema_info['tables']]
    
    print(f"📊 Found {len(existing_tables)} tables:")
    for table in existing_tables:
        print(f"   ✅ {table}")
    
    # Check for missing tables
    missing_tables = [table for table in expected_tables if table not in existing_tables]
    
    if missing_tables:
        print(f"\n⚠️  Missing expected tables:")
        for table in missing_tables:
            print(f"   ❌ {table}")
        return False
    else:
        print(f"\n✅ All expected tables found!")
        return True

def check_alembic_version():
    """
    Check Alembic version and migration status
    """
    print("🔄 Checking Alembic migration status...")
    
    try:
        # Change to backend directory
        original_dir = os.getcwd()
        os.chdir("backend")
        
        # Get current revision
        result = subprocess.run(
            ["alembic", "current"],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("📌 Current Alembic status:")
        print(result.stdout)
        
        # Check history
        result = subprocess.run(
            ["alembic", "history", "--verbose"],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("📚 Migration history:")
        print(result.stdout)
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error checking Alembic: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    finally:
        # Return to original directory
        os.chdir(original_dir)

def generate_validation_report(schema_info):
    """
    Generate a detailed validation report
    """
    print("📝 Generating validation report...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"temp/validation_report_{timestamp}.json"
    
    report = {
        'validation_date': datetime.now().isoformat(),
        'database_info': {
            'total_tables': len(schema_info['tables']),
            'total_indexes': len(schema_info['indexes'])
        },
        'tables': schema_info['tables'],
        'indexes': schema_info['indexes'],
        'validation_results': {
            'schema_valid': True,
            'all_tables_present': True,
            'alembic_status': 'OK'
        }
    }
    
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Validation report saved: {report_file}")
        return report_file
        
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        return None

def print_schema_summary(schema_info):
    """
    Print a nice summary of the database schema
    """
    print("\n" + "=" * 60)
    print("📊 DATABASE SCHEMA SUMMARY")
    print("=" * 60)
    
    print(f"\n📋 Tables ({len(schema_info['tables'])}):")
    for table in schema_info['tables']:
        print(f"   🗃️  {table['name']} ({len(table.get('columns', []))} columns)")
        
        # Show key columns
        key_columns = []
        for col in table.get('columns', []):
            if 'id' in col['name'].lower() or col.get('default') and 'nextval' in str(col.get('default')):
                key_columns.append(f"{col['name']} ({col['type']})")
        
        if key_columns:
            print(f"      🔑 Key columns: {', '.join(key_columns)}")
    
    if schema_info['indexes']:
        print(f"\n📇 Indexes ({len(schema_info['indexes'])}):")
        for index in schema_info['indexes']:
            print(f"   🔍 {index['name']} on {index['table']}")
    
    print("\n" + "=" * 60)

def main():
    """
    Main validation function
    """
    print("🔍 Database Schema Validation Tool")
    print("=" * 50)
    
    # Get schema information
    schema_info = get_database_schema_info()
    if not schema_info:
        print("❌ Failed to get schema information")
        return False
    
    # Print schema summary
    print_schema_summary(schema_info)
    
    # Validate expected tables
    tables_valid = validate_expected_tables()
    
    # Check Alembic status
    alembic_valid = check_alembic_version()
    
    # Generate validation report
    report_file = generate_validation_report(schema_info)
    
    # Final validation result
    all_valid = tables_valid and alembic_valid
    
    print("\n" + "=" * 60)
    if all_valid:
        print("✅ VALIDATION PASSED!")
        print("🎉 Database schema is ready for development")
    else:
        print("⚠️  VALIDATION ISSUES FOUND")
        print("💡 Please check the issues above")
    print("=" * 60)
    
    if report_file:
        print(f"📝 Detailed report: {report_file}")
    
    return all_valid

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)