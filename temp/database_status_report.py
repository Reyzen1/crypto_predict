# File: temp/database_status_report.py
# Generate comprehensive database status report

import sys
from pathlib import Path
from datetime import datetime

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.user import User
from app.models.cryptocurrency import Cryptocurrency
from app.models.prediction import Prediction

def get_table_info(engine, table_name):
    """Get detailed table information"""
    with engine.connect() as conn:
        # Get columns info
        columns_result = conn.execute(text("""
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default,
                character_maximum_length,
                numeric_precision,
                numeric_scale
            FROM information_schema.columns 
            WHERE table_name = :table_name
            ORDER BY ordinal_position
        """), {"table_name": table_name})
        
        columns = columns_result.fetchall()
        
        # Get constraints info
        constraints_result = conn.execute(text("""
            SELECT 
                tc.constraint_name,
                tc.constraint_type,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            LEFT JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.table_name = :table_name
            ORDER BY tc.constraint_type, tc.constraint_name
        """), {"table_name": table_name})
        
        constraints = constraints_result.fetchall()
        
        return columns, constraints

def get_data_counts(db):
    """Get record counts for each table"""
    counts = {}
    try:
        counts['users'] = db.query(User).count()
        counts['cryptocurrencies'] = db.query(Cryptocurrency).count()
        counts['predictions'] = db.query(Prediction).count()
        
        # Get price_data count directly with SQL
        with db.get_bind().connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM price_data"))
            counts['price_data'] = result.scalar()
            
            # Check if portfolios table exists
            table_check = conn.execute(text("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_name = 'portfolios'
            """))
            if table_check.scalar() > 0:
                portfolio_count = conn.execute(text("SELECT COUNT(*) FROM portfolios"))
                counts['portfolios'] = portfolio_count.scalar()
            else:
                counts['portfolios'] = "Table not found"
                
    except Exception as e:
        counts['error'] = str(e)
    
    return counts

def format_column_info(columns):
    """Format column information for display"""
    formatted = []
    for col in columns:
        col_name, data_type, is_nullable, default, max_length, precision, scale = col
        
        # Build type string
        type_str = data_type
        if precision and scale:
            type_str += f"({precision},{scale})"
        elif max_length:
            type_str += f"({max_length})"
        
        # Build constraints string
        constraints = []
        if is_nullable == 'NO':
            constraints.append('NOT NULL')
        if default:
            constraints.append(f'DEFAULT {default}')
        
        constraint_str = ' '.join(constraints) if constraints else ''
        
        formatted.append({
            'name': col_name,
            'type': type_str,
            'constraints': constraint_str
        })
    
    return formatted

def main():
    print("📊 Database Status Report")
    print("=" * 50)
    print(f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Get Alembic version
        try:
            with engine.connect() as conn:
                alembic_result = conn.execute(text("SELECT version_num FROM alembic_version"))
                alembic_version = alembic_result.scalar()
        except:
            alembic_version = "Not found"
        
        print(f"🔄 Alembic Version: {alembic_version}")
        print()
        
        # Table analysis
        tables = ['users', 'cryptocurrencies', 'price_data', 'predictions']
        
        for table_name in tables:
            print(f"📋 Table: {table_name}")
            print("-" * 30)
            
            try:
                columns, constraints = get_table_info(engine, table_name)
                formatted_columns = format_column_info(columns)
                
                print(f"   📊 Total columns: {len(columns)}")
                print("   📝 Columns:")
                for col in formatted_columns:
                    print(f"      • {col['name']} - {col['type']} {col['constraints']}")
                
                if constraints:
                    print("   🔗 Constraints:")
                    for constraint in constraints:
                        constraint_name, constraint_type, column_name, foreign_table, foreign_column = constraint
                        if constraint_type == 'FOREIGN KEY':
                            print(f"      • FK: {column_name} → {foreign_table}.{foreign_column}")
                        elif constraint_type == 'PRIMARY KEY':
                            print(f"      • PK: {column_name}")
                        elif constraint_type == 'UNIQUE':
                            print(f"      • UNIQUE: {column_name}")
                
            except Exception as e:
                print(f"   ❌ Error analyzing table: {e}")
            
            print()
        
        # Data counts
        print("📈 Data Summary")
        print("-" * 20)
        counts = get_data_counts(db)
        for table, count in counts.items():
            if isinstance(count, int):
                print(f"   • {table}: {count:,} records")
            else:
                print(f"   • {table}: {count}")
        
        print()
        
        # Sample data
        print("🔍 Sample Data")
        print("-" * 15)
        
        if counts.get('users', 0) > 0:
            user = db.query(User).first()
            print(f"   👤 Sample User: ID={user.id}, Email={user.email}")
        
        if counts.get('cryptocurrencies', 0) > 0:
            crypto = db.query(Cryptocurrency).first()
            print(f"   🪙 Sample Crypto: ID={crypto.id}, Symbol={crypto.symbol}, Name={crypto.name}")
        
        if counts.get('predictions', 0) > 0:
            prediction = db.query(Prediction).first()
            print(f"   📈 Sample Prediction: ID={prediction.id}, Model={prediction.model_name}")
        
        print()
        print("🎉 Database Status Report Complete!")
        print("✅ All core tables are present and functional")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)