# Fallback training method for MLTrainingService

# Add this method to MLTrainingService class as a fallback

async def train_model_for_crypto_simple(
    self,
    crypto_symbol: str,
    training_config: Optional[Dict[str, Any]] = None,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """Simple, robust training method as fallback"""
    
    try:
        logger.info(f"Starting simple training for {crypto_symbol}")
        
        # Get training data from database
        if db is None:
            db = SessionLocal()
            should_close_db = True
        else:
            should_close_db = False
        
        try:
            # Get crypto record
            crypto = cryptocurrency_repository.get_by_symbol(db, crypto_symbol)
            if not crypto:
                raise ValueError(f"Cryptocurrency {crypto_symbol} not found")
            
            # Get price data
            training_df = ml_repository.get_training_data_for_crypto(
                db=db,
                crypto_id=crypto.id,
                days_back=30,
                min_records=50
            )
            
            if training_df.empty or len(training_df) < 50:
                raise ValueError(f"Insufficient training data: {len(training_df)} records")
            
            # Simple LSTM training with minimal config
            lstm_model = LSTMPredictor(
                sequence_length=20,
                n_features=3,
                lstm_units=[16, 16],
                epochs=3,
                batch_size=16
            )
            
            # Prepare data
            X, y, target_scaler, feature_scaler = lstm_model.prepare_data(training_df)
            
            # Simple train/val split
            train_size = int(0.8 * len(X))
            X_train, X_val = X[:train_size], X[train_size:]
            y_train, y_val = y[:train_size], y[train_size:]
            
            # Train model
            training_metrics = lstm_model.train(X_train, y_train, X_val, y_val, save_model=False)
            
            # Simple success result
            model_id = f"{crypto_symbol}_simple_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            result = {
                'success': True,
                'crypto_symbol': crypto_symbol,
                'model_id': model_id,
                'message': 'Simple training completed successfully',
                'training_metrics': training_metrics,
                'data_points_used': len(training_df),
                'features_count': lstm_model.n_features,
                'training_duration': training_metrics.get('training_duration_seconds', 0)
            }
            
            return result
            
        finally:
            if should_close_db:
                db.close()
        
    except Exception as e:
        logger.error(f"Simple training failed for {crypto_symbol}: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'crypto_symbol': crypto_symbol,
            'message': f'Simple training failed: {str(e)}'
        }
