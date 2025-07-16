#!/usr/bin/env python3
"""
File: scripts/check-db.py
Database health check script for CryptoPredict MVP
Tests PostgreSQL and Redis connections
"""

import sys
import time
import psycopg2
import redis
from typing import Tuple, Optional
import os
from urllib.parse import urlparse

# ANSI color codes
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_status(message: str, status: str = "INFO") -> None:
    """Print colored status message"""
    color_map = {
        "INFO": Colors.BLUE,
        "SUCCESS": Colors.GREEN,
        "WARNING": Colors.YELLOW,
        "ERROR": Colors.RED
    }
    color = color_map.get(status, Colors.BLUE)
    print(f"{color}[{status}]{Colors.END} {message}")

def parse_postgres_url(url: str) -> dict:
    """Parse PostgreSQL connection URL"""
    try:
        parsed = urlparse(url)
        return {
            'host': parsed.hostname or 'localhost',
            'port': parsed.port or 5432,
            'database': parsed.path.lstrip('/') or 'cryptopredict',
            'user': parsed.username or 'postgres',
            'password': parsed.password or 'postgres123'
        }
    except Exception as e:
        print_status(f"Error parsing PostgreSQL URL: {e}", "ERROR")
        return {}

def parse_redis_url(url: str) -> dict:
    """Parse Redis connection URL"""
    try:
        parsed = urlparse(url)
        return {
            'host': parsed.hostname or 'localhost',
            'port': parsed.port or 6379,
            'db': int(parsed.path.lstrip('/')) if parsed.path.lstrip('/') else 0,
            'password': parsed.password
        }
    except Exception as e:
        print_status(f"Error parsing Redis URL: {e}", "ERROR")
        return {}

def check_postgres(connection_params: dict, max_retries: int = 5) -> Tuple[bool, Optional[str]]:
    """Check PostgreSQL connection and basic functionality"""
    print_status("Checking PostgreSQL connection...")
    
    for attempt in range(1, max_retries + 1):
        try:
            # Connect to PostgreSQL
            conn = psycopg2.connect(**connection_params)
            cursor = conn.cursor()
            
            # Test basic query
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            
            # Test database exists
            cursor.execute("SELECT datname FROM pg_database WHERE datname = %s;", 
                         (connection_params['database'],))
            db_exists = cursor.fetchone() is not None
            
            # Test table creation (if database exists)
            if db_exists:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS health_check_test (
                        id SERIAL PRIMARY KEY,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                
                # Test insert
                cursor.execute("INSERT INTO health_check_test DEFAULT VALUES RETURNING id;")
                test_id = cursor.fetchone()[0]
                
                # Test select
                cursor.execute("SELECT COUNT(*) FROM health_check_test;")
                count = cursor.fetchone()[0]
                
                # Clean up test data
                cursor.execute("DROP TABLE IF EXISTS health_check_test;")
                
                conn.commit()
                print_status(f"PostgreSQL connection successful! Version: {version[:50]}...", "SUCCESS")
                print_status(f"Database operations test passed (inserted record {test_id}, total records: {count})", "SUCCESS")
            else:
                print_status(f"Database '{connection_params['database']}' does not exist", "WARNING")
            
            cursor.close()
            conn.close()
            return True, version
            
        except psycopg2.OperationalError as e:
            if attempt < max_retries:
                print_status(f"PostgreSQL connection attempt {attempt}/{max_retries} failed, retrying in 2 seconds...", "WARNING")
                time.sleep(2)
            else:
                print_status(f"PostgreSQL connection failed after {max_retries} attempts: {e}", "ERROR")
                return False, str(e)
        except Exception as e:
            print_status(f"PostgreSQL error: {e}", "ERROR")
            return False, str(e)
    
    return False, "Max retries exceeded"

def check_redis(connection_params: dict, max_retries: int = 5) -> Tuple[bool, Optional[str]]:
    """Check Redis connection and basic functionality"""
    print_status("Checking Redis connection...")
    
    for attempt in range(1, max_retries + 1):
        try:
            # Connect to Redis
            r = redis.Redis(**connection_params, decode_responses=True)
            
            # Test ping
            pong = r.ping()
            if not pong:
                raise redis.ConnectionError("Ping failed")
            
            # Test basic operations
            test_key = "health_check_test"
            test_value = f"test_value_{int(time.time())}"
            
            # Test set
            r.set(test_key, test_value, ex=10)  # Expire in 10 seconds
            
            # Test get
            retrieved_value = r.get(test_key)
            
            if retrieved_value != test_value:
                raise ValueError(f"Value mismatch: expected {test_value}, got {retrieved_value}")
            
            # Test delete
            r.delete(test_key)
            
            # Get Redis info
            info = r.info()
            redis_version = info.get('redis_version', 'Unknown')
            used_memory = info.get('used_memory_human', 'Unknown')
            
            print_status(f"Redis connection successful! Version: {redis_version}", "SUCCESS")
            print_status(f"Redis memory usage: {used_memory}", "SUCCESS")
            
            return True, f"Redis {redis_version}"
            
        except (redis.ConnectionError, redis.TimeoutError) as e:
            if attempt < max_retries:
                print_status(f"Redis connection attempt {attempt}/{max_retries} failed, retrying in 2 seconds...", "WARNING")
                time.sleep(2)
            else:
                print_status(f"Redis connection failed after {max_retries} attempts: {e}", "ERROR")
                return False, str(e)
        except Exception as e:
            print_status(f"Redis error: {e}", "ERROR")
            return False, str(e)
    
    return False, "Max retries exceeded"

def check_environment() -> Tuple[str, str]:
    """Get database connection strings from environment"""
    # PostgreSQL URL
    postgres_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres123@localhost:5432/cryptopredict')
    
    # Redis URL
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    print_status(f"Using PostgreSQL URL: {postgres_url}", "INFO")
    print_status(f"Using Redis URL: {redis_url}", "INFO")
    
    return postgres_url, redis_url

def main() -> None:
    """Main health check function"""
    print_status("=" * 50)
    print_status("CryptoPredict MVP Database Health Check")
    print_status("=" * 50)
    
    # Get connection strings
    postgres_url, redis_url = check_environment()
    
    # Parse connection parameters
    postgres_params = parse_postgres_url(postgres_url)
    redis_params = parse_redis_url(redis_url)
    
    if not postgres_params or not redis_params:
        print_status("Failed to parse connection parameters", "ERROR")
        sys.exit(1)
    
    # Check connections
    postgres_ok, postgres_info = check_postgres(postgres_params)
    redis_ok, redis_info = check_redis(redis_params)
    
    # Summary
    print_status("=" * 50)
    print_status("Health Check Summary:")
    print_status(f"PostgreSQL: {'✓ HEALTHY' if postgres_ok else '✗ UNHEALTHY'}", 
                "SUCCESS" if postgres_ok else "ERROR")
    print_status(f"Redis: {'✓ HEALTHY' if redis_ok else '✗ UNHEALTHY'}", 
                "SUCCESS" if redis_ok else "ERROR")
    print_status("=" * 50)
    
    if postgres_ok and redis_ok:
        print_status("All database services are healthy! 🎉", "SUCCESS")
        sys.exit(0)
    else:
        print_status("Some database services are unhealthy! 🚨", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_status("\nHealth check interrupted by user", "WARNING")
        sys.exit(1)
    except Exception as e:
        print_status(f"Unexpected error: {e}", "ERROR")
        sys.exit(1)