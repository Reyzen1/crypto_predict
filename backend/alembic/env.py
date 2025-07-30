# File: backend/alembic/env.py
# Alembic environment configuration with dynamic database URL

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Import app modules
from app.core.database import Base
from app.models import User, Cryptocurrency, PriceData, Prediction

# Load environment variables
try:
    from dotenv import load_dotenv
    # Look for .env in project root (one level up from backend)
    env_path = backend_dir.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
    else:
        # Fallback to backend directory
        load_dotenv(backend_dir / '.env')
except ImportError:
    pass

# this is the Alembic Config object, which provides
# access to the values within the .env file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_database_url():
    """Get database URL from environment variable"""
    
    # Try to get from environment variable first
    database_url = os.getenv('DATABASE_URL')
    
    if database_url:
        return database_url
    
    # If not found, try to import from config
    try:
        from app.core.config import settings
        return settings.DATABASE_URL
    except ImportError:
        pass
    
    # Fallback to default for development
    return "postgresql://postgres:admin123@localhost:5433/cryptopredict"


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    
    # Get database URL
    database_url = get_database_url()
    
    # Override the sqlalchemy.url in the alembic configuration
    config.set_main_option('sqlalchemy.url', database_url)
    
    # Create engine
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()