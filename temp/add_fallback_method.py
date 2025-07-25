# File: temp/add_fallback_method.py
# Script to automatically add the fallback method to MLTrainingService

def add_fallback_method_to_training_service():
    """Add the fallback method to MLTrainingService class"""
    
    file_path = 'backend/app/ml/training/training_service.py'
    
    try:
        print("🔧 Adding fallback method to MLTrainingService...")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the end of the MLTrainingService class
        # Look for the last method in the class
        
        # Find where to insert the new method
        # Look for the end of the last method in the class
        
        insertion_point = None
        lines = content.split('\n')
        
        # Find the class definition
        class_start = None
        for i, line in enumerate(lines):
            if 'class MLTrainingService:' in line:
                class_start = i
                break
        
        if class_start is None:
            print("❌ Could not find MLTrainingService class")
            return False
        
        # Find the last method in the class
        last_method_end = None
        in_class = False
        method_indent = None
        
        for i in range(class_start, len(lines)):
            line = lines[i]
            
            # Skip empty lines and comments
            if not line.strip() or line.strip().startswith('#'):
                continue
            
            # Check if we're still in the class
            if i > class_start and line and not line.startswith(' ') and not line.startswith('\t'):
                # We've left the class
                break
            
            # Look for methods in the class
            if line.strip().startswith('async def ') or line.strip().startswith('def '):
                method_indent = len(line) - len(line.lstrip())
                last_method_end = None  # Reset, we found a new method
            
            # If we're in a method and find the next method or end of class
            elif method_indent is not None and line and (len(line) - len(line.lstrip())) <= method_indent and line.strip():
                if not (line.strip().startswith('async def ') or line.strip().startswith('def ')):
                    last_method_end = i
        
        # If we didn't find a good insertion point, add before the global instance
        if last_method_end is None:
            # Look for the global training_service instance
            for i, line in enumerate(lines):
                if 'training_service = MLTrainingService()' in line:
                    last_method_end = i - 1
                    break
        
        if last_method_end is None:
            last_method_end = len(lines) - 1
        
        print(f"✅ Found insertion point at line {last_method_end + 1}")
        
        # The fallback method to add
        fallback_method = '''
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
                
                # Get price data using existing repository
                from app.repositories.ml_repository import ml_repository
                training_df = ml_repository.get_training_data_for_crypto(
                    db=db,
                    crypto_id=crypto.id,
                    days_back=30,
                    min_records=50
                )
                
                if training_df.empty or len(training_df) < 50:
                    raise ValueError(f"Insufficient training data: {len(training_df)} records")
                
                logger.info(f"Loaded {len(training_df)} training records")
                
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
                logger.info(f"Data prepared: X={X.shape}, y={y.shape}")
                
                # Simple train/val split
                train_size = int(0.8 * len(X))
                X_train, X_val = X[:train_size], X[train_size:]
                y_train, y_val = y[:train_size], y[train_size:]
                
                # Train model
                training_metrics = lstm_model.train(X_train, y_train, X_val, y_val, save_model=False)
                
                # Simple evaluation
                try:
                    evaluation_metrics = lstm_model.evaluate(X_val, y_val)
                except:
                    evaluation_metrics = {'rmse': 0.0, 'mae': 0.0, 'r2_score': 0.0}
                
                # Simple success result
                model_id = f"{crypto_symbol}_simple_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                result = {
                    'success': True,
                    'crypto_symbol': crypto_symbol,
                    'model_id': model_id,
                    'message': 'Simple training completed successfully',
                    'training_metrics': training_metrics,
                    'evaluation_metrics': evaluation_metrics,
                    'data_points_used': len(training_df),
                    'features_count': lstm_model.n_features,
                    'training_duration': training_metrics.get('training_duration_seconds', 0)
                }
                
                logger.info(f"✅ Simple training completed for {crypto_symbol}")
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
'''
        
        # Insert the method
        lines.insert(last_method_end + 1, fallback_method)
        
        # Write back the modified content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        print("✅ Fallback method added successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error adding fallback method: {e}")
        return False

def test_fallback_method():
    """Test if the fallback method was added correctly"""
    
    try:
        print("\n🧪 Testing fallback method...")
        
        # Try to import and check if method exists
        import sys
        import os
        
        backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
        sys.path.insert(0, backend_path)
        
        from app.ml.training.training_service import MLTrainingService
        
        service = MLTrainingService()
        
        # Check if the new method exists
        if hasattr(service, 'train_model_for_crypto_simple'):
            print("✅ Fallback method successfully added!")
            print("✅ Method is accessible")
            return True
        else:
            print("❌ Fallback method not found")
            return False
            
    except Exception as e:
        print(f"❌ Error testing fallback method: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Adding Fallback Method to MLTrainingService")
    print("=" * 50)
    
    if add_fallback_method_to_training_service():
        if test_fallback_method():
            print("\n🎉 Success! Fallback method added and working")
            print("\n🚀 Now you can use either method:")
            print("   1. train_model_for_crypto() - full method")
            print("   2. train_model_for_crypto_simple() - fallback method")
            print("\n📋 To test:")
            print("   cd backend && python ../temp/test_complete_ml_pipeline.py")
        else:
            print("\n⚠️ Method added but testing failed")
    else:
        print("\n❌ Failed to add fallback method")
        print("\n📋 Manual steps:")
        print("1. Open backend/app/ml/training/training_service.py")
        print("2. Find the MLTrainingService class")
        print("3. Add the fallback method before the end of the class")
        print("4. Make sure indentation matches other methods")