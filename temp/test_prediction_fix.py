# File: temp/test_prediction_fix.py
# Test prediction creation after schema fix

import sys
import os
from datetime import datetime, timezone, timedelta

# Add backend path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

def test_prediction_schema():
    """Test if prediction schema works correctly"""
    
    try:
        from app.schemas.prediction import PredictionCreate
        from decimal import Decimal
        
        # Test data
        prediction_data = {
            'crypto_id': 1,
            'user_id': 1,
            'model_name': 'LSTM_test',
            'predicted_price': Decimal('50000.00'),
            'confidence_score': Decimal('0.85'),
            'target_datetime': datetime.now(timezone.utc) + timedelta(hours=24),
            'features_used': '{"feature1": "value1"}'
        }
        
        # Try to create prediction schema
        prediction = PredictionCreate(**prediction_data)
        
        print("✅ PredictionCreate schema works!")
        print(f"   - target_datetime: {prediction.target_datetime}")
        print(f"   - predicted_price: {prediction.predicted_price}")
        print(f"   - confidence_score: {prediction.confidence_score}")
        
        return True
        
    except Exception as e:
        print(f"❌ Schema test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Prediction Schema Fix")
    print("=" * 40)
    test_prediction_schema()
