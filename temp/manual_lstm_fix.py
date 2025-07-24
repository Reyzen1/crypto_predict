# File: temp/manual_lstm_fix.py
# Manual fix for LSTM predictor if automatic fix fails

def apply_manual_fix():
    """Apply manual fix to lstm_predictor.py"""
    
    file_path = 'backend/app/ml/models/lstm_predictor.py'
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Find and fix problematic lines
        for i, line in enumerate(lines):
            # Fix the specific syntax error on line 502
            if 'y_true = self.scaler.inverse_transform(y_test.reshape(-1, 1) if self.scaler is not None else y_test.reshape(-1, 1).flatten()' in line:
                lines[i] = '        y_true = self.scaler.inverse_transform(y_test.reshape(-1, 1)).flatten() if self.scaler is not None else y_test.flatten()\n'
                print(f"✅ Fixed line {i+1}")
            
            # Fix similar issues with predictions
            elif 'predictions_actual = self.scaler.inverse_transform(predictions_scaled) if self.scaler is not None else predictions_scaled' in line:
                lines[i] = '        predictions_actual = self.scaler.inverse_transform(predictions_scaled).flatten() if self.scaler is not None else predictions_scaled.flatten()\n'
                print(f"✅ Fixed line {i+1}")
        
        # Write back the fixed content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print("✅ Manual fix applied")
        return True
        
    except Exception as e:
        print(f"❌ Manual fix failed: {e}")
        return False

if __name__ == "__main__":
    apply_manual_fix()
