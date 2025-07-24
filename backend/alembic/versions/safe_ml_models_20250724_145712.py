"""Safe migration for ML models with existing data

Revision ID: safe_ml_models_20250724_145712
Revises: 
Create Date: 2025-07-24T14:57:12.166195

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'safe_ml_models_20250724_145712'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Safely create/update ML model tables"""
    
    # Check if cryptocurrencies table exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()
    
    if 'cryptocurrencies' not in existing_tables:
        # Create new cryptocurrencies table
        op.create_table('cryptocurrencies',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('symbol', sa.String(length=10), nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('coingecko_id', sa.String(length=50), nullable=True),
            sa.Column('market_cap_rank', sa.Integer(), nullable=True),
            sa.Column('current_price', sa.Numeric(precision=20, scale=8), nullable=True),
            sa.Column('market_cap', sa.Numeric(precision=30, scale=2), nullable=True),
            sa.Column('total_volume', sa.Numeric(precision=30, scale=2), nullable=True),
            sa.Column('circulating_supply', sa.Numeric(precision=30, scale=2), nullable=True),
            sa.Column('total_supply', sa.Numeric(precision=30, scale=2), nullable=True),
            sa.Column('max_supply', sa.Numeric(precision=30, scale=2), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('website_url', sa.String(length=255), nullable=True),
            sa.Column('blockchain_site', sa.String(length=255), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
            sa.Column('is_supported', sa.Boolean(), nullable=False, default=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('last_data_update', sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        
        # Create indexes for new table
        op.create_index('idx_crypto_symbol_active', 'cryptocurrencies', ['symbol', 'is_active'])
        op.create_index('idx_crypto_rank', 'cryptocurrencies', ['market_cap_rank'])
        op.create_index('idx_crypto_updated', 'cryptocurrencies', ['updated_at'])
        op.create_index(op.f('ix_cryptocurrencies_id'), 'cryptocurrencies', ['id'])
        op.create_index(op.f('ix_cryptocurrencies_symbol'), 'cryptocurrencies', ['symbol'], unique=True)
        op.create_index(op.f('ix_cryptocurrencies_coingecko_id'), 'cryptocurrencies', ['coingecko_id'], unique=True)
        
    else:
        # Update existing cryptocurrencies table safely
        existing_columns = [col['name'] for col in inspector.get_columns('cryptocurrencies')]
        
        # Add missing columns one by one with default values
        new_columns = [
            ('coingecko_id', sa.String(length=50), None),
            ('market_cap_rank', sa.Integer(), None),
            ('current_price', sa.Numeric(precision=20, scale=8), None),
            ('market_cap', sa.Numeric(precision=30, scale=2), None),
            ('total_volume', sa.Numeric(precision=30, scale=2), None),
            ('circulating_supply', sa.Numeric(precision=30, scale=2), None),
            ('total_supply', sa.Numeric(precision=30, scale=2), None),
            ('max_supply', sa.Numeric(precision=30, scale=2), None),
            ('description', sa.Text(), None),
            ('website_url', sa.String(length=255), None),
            ('blockchain_site', sa.String(length=255), None),
            ('is_active', sa.Boolean(), True),
            ('is_supported', sa.Boolean(), True),
            ('created_at', sa.DateTime(timezone=True), 'now()'),
            ('updated_at', sa.DateTime(timezone=True), 'now()'),
            ('last_data_update', sa.DateTime(timezone=True), None),
        ]
        
        for column_name, column_type, default_value in new_columns:
            if column_name not in existing_columns:
                if default_value is not None:
                    if isinstance(default_value, bool):
                        # Add boolean column with default value
                        op.add_column('cryptocurrencies', 
                                    sa.Column(column_name, column_type, nullable=True))
                        # Update all existing rows with default value
                        op.execute(f"UPDATE cryptocurrencies SET {column_name} = {'true' if default_value else 'false'}")
                        # Make column NOT NULL after setting values
                        op.alter_column('cryptocurrencies', column_name, nullable=False)
                    elif default_value == 'now()':
                        # Add datetime column with server default
                        op.add_column('cryptocurrencies', 
                                    sa.Column(column_name, column_type, 
                                            server_default=sa.text('now()'), nullable=False))
                else:
                    # Add nullable column
                    op.add_column('cryptocurrencies', 
                                sa.Column(column_name, column_type, nullable=True))
        
        # Create missing indexes
        try:
            op.create_index('idx_crypto_symbol_active', 'cryptocurrencies', ['symbol', 'is_active'])
        except:
            pass  # Index might already exist
        
        try:
            op.create_index('idx_crypto_rank', 'cryptocurrencies', ['market_cap_rank'])
        except:
            pass
            
        try:
            op.create_index('idx_crypto_updated', 'cryptocurrencies', ['updated_at'])
        except:
            pass

    # Create price_data table if it doesn't exist
    if 'price_data' not in existing_tables:
        op.create_table('price_data',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('crypto_id', sa.Integer(), nullable=False),
            sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
            sa.Column('open_price', sa.Numeric(precision=20, scale=8), nullable=False),
            sa.Column('high_price', sa.Numeric(precision=20, scale=8), nullable=False),
            sa.Column('low_price', sa.Numeric(precision=20, scale=8), nullable=False),
            sa.Column('close_price', sa.Numeric(precision=20, scale=8), nullable=False),
            sa.Column('volume', sa.Numeric(precision=30, scale=8), nullable=False),
            sa.Column('market_cap', sa.Numeric(precision=30, scale=2), nullable=True),
            sa.Column('total_volume', sa.Numeric(precision=30, scale=2), nullable=True),
            sa.Column('sma_20', sa.Numeric(precision=20, scale=8), nullable=True),
            sa.Column('sma_50', sa.Numeric(precision=20, scale=8), nullable=True),
            sa.Column('ema_12', sa.Numeric(precision=20, scale=8), nullable=True),
            sa.Column('ema_26', sa.Numeric(precision=20, scale=8), nullable=True),
            sa.Column('rsi', sa.Numeric(precision=5, scale=2), nullable=True),
            sa.Column('macd', sa.Numeric(precision=20, scale=8), nullable=True),
            sa.Column('macd_signal', sa.Numeric(precision=20, scale=8), nullable=True),
            sa.Column('bollinger_upper', sa.Numeric(precision=20, scale=8), nullable=True),
            sa.Column('bollinger_lower', sa.Numeric(precision=20, scale=8), nullable=True),
            sa.Column('price_change_1h', sa.Numeric(precision=10, scale=4), nullable=True),
            sa.Column('price_change_24h', sa.Numeric(precision=10, scale=4), nullable=True),
            sa.Column('price_change_7d', sa.Numeric(precision=10, scale=4), nullable=True),
            sa.Column('data_source', sa.String(length=50), nullable=False, default='coingecko'),
            sa.Column('data_interval', sa.String(length=10), nullable=False, default='1h'),
            sa.Column('is_validated', sa.Boolean(), nullable=False, default=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['crypto_id'], ['cryptocurrencies.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        
        # Create indexes for price_data
        op.create_index('idx_price_crypto_timestamp', 'price_data', ['crypto_id', 'timestamp'])
        op.create_index('idx_price_interval', 'price_data', ['data_interval', 'timestamp'])
        op.create_index('idx_price_source', 'price_data', ['data_source', 'created_at'])
        op.create_index('idx_price_unique', 'price_data', ['crypto_id', 'timestamp', 'data_interval'], unique=True)
        op.create_index(op.f('ix_price_data_id'), 'price_data', ['id'])
        op.create_index(op.f('ix_price_data_crypto_id'), 'price_data', ['crypto_id'])
        op.create_index(op.f('ix_price_data_timestamp'), 'price_data', ['timestamp'])

    # Create predictions table if it doesn't exist
    if 'predictions' not in existing_tables:
        op.create_table('predictions',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('crypto_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('model_name', sa.String(length=50), nullable=False),
            sa.Column('model_version', sa.String(length=20), nullable=False, default='1.0'),
            sa.Column('predicted_price', sa.Numeric(precision=20, scale=8), nullable=False),
            sa.Column('confidence_score', sa.Numeric(precision=5, scale=4), nullable=False),
            sa.Column('prediction_horizon', sa.Integer(), nullable=False),
            sa.Column('target_datetime', sa.DateTime(timezone=True), nullable=False),
            sa.Column('features_used', sa.JSON(), nullable=True),
            sa.Column('model_parameters', sa.JSON(), nullable=True),
            sa.Column('input_price', sa.Numeric(precision=20, scale=8), nullable=False),
            sa.Column('input_features', sa.JSON(), nullable=True),
            sa.Column('actual_price', sa.Numeric(precision=20, scale=8), nullable=True),
            sa.Column('accuracy_percentage', sa.Numeric(precision=5, scale=2), nullable=True),
            sa.Column('absolute_error', sa.Numeric(precision=20, scale=8), nullable=True),
            sa.Column('squared_error', sa.Numeric(precision=30, scale=8), nullable=True),
            sa.Column('is_realized', sa.Boolean(), nullable=False, default=False),
            sa.Column('is_accurate', sa.Boolean(), nullable=True),
            sa.Column('accuracy_threshold', sa.Numeric(precision=5, scale=2), default=5.0),
            sa.Column('training_data_end', sa.DateTime(timezone=True), nullable=True),
            sa.Column('market_conditions', sa.String(length=20), nullable=True),
            sa.Column('volatility_level', sa.String(length=10), nullable=True),
            sa.Column('model_training_time', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('prediction_time', sa.Numeric(precision=10, scale=6), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('debug_info', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('evaluated_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['crypto_id'], ['cryptocurrencies.id'], ),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        
        # Create indexes for predictions
        op.create_index('idx_prediction_crypto_target', 'predictions', ['crypto_id', 'target_datetime'])
        op.create_index('idx_prediction_model_created', 'predictions', ['model_name', 'created_at'])
        op.create_index('idx_prediction_user_created', 'predictions', ['user_id', 'created_at'])
        op.create_index('idx_prediction_horizon', 'predictions', ['prediction_horizon', 'created_at'])
        op.create_index('idx_prediction_realized', 'predictions', ['is_realized', 'accuracy_percentage'])
        op.create_index('idx_prediction_model_performance', 'predictions', ['model_name', 'model_version', 'confidence_score'])
        op.create_index(op.f('ix_predictions_id'), 'predictions', ['id'])
        op.create_index(op.f('ix_predictions_crypto_id'), 'predictions', ['crypto_id'])
        op.create_index(op.f('ix_predictions_user_id'), 'predictions', ['user_id'])
        op.create_index(op.f('ix_predictions_model_name'), 'predictions', ['model_name'])
        op.create_index(op.f('ix_predictions_target_datetime'), 'predictions', ['target_datetime'])
        op.create_index(op.f('ix_predictions_created_at'), 'predictions', ['created_at'])


def downgrade() -> None:
    """Remove ML model tables and columns"""
    # Drop tables created in this migration
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()
    
    if 'predictions' in existing_tables:
        op.drop_table('predictions')
    
    if 'price_data' in existing_tables:
        op.drop_table('price_data')
    
    # For cryptocurrencies table, only remove columns added in this migration
    # (Don't drop the whole table as it might have been created in a previous migration)
