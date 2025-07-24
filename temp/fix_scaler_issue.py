# File: temp/fix_scaler_issue.py
# اسکریپت اصلاح فوری مشکل MinMaxScaler

import sys
import os
sys.path.append('.')

def apply_scaler_fix():
    """اصلاح مشکل MinMaxScaler در lstm_predictor.py"""
    
    lstm_file_path = 'backend/app/ml/models/lstm_predictor.py'
    
    try:
        # خواندن فایل فعلی
        with open(lstm_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("🔧 اصلاح مشکل MinMaxScaler...")
        
        # اصلاح 1: جایگزین کردن fillna deprecated
        old_fillna = "data[feature_columns] = data[feature_columns].fillna(method='ffill').fillna(method='bfill')"
        new_fillna = """# Handle missing values with modern pandas methods
        for col in feature_columns:
            if col in data.columns:
                data[col] = data[col].ffill().bfill()"""
        
        if old_fillna in content:
            content = content.replace(old_fillna, new_fillna)
            print("✅ اصلاح fillna deprecated")
        
        # اصلاح 2: بهبود prepare_data method
        # پیدا کردن شروع method prepare_data
        start_marker = "def prepare_data("
        end_marker = "return X, y, self.scaler, self.feature_scaler"
        
        start_pos = content.find(start_marker)
        if start_pos != -1:
            # پیدا کردن انتهای method
            end_pos = content.find(end_marker, start_pos)
            if end_pos != -1:
                end_pos = content.find('\n', end_pos) + 1
                
                # method جدید
                new_prepare_data = '''def prepare_data(
        self, 
        data: pd.DataFrame, 
        target_column: str = 'close_price',
        feature_columns: Optional[List[str]] = None
    ) -> Tuple[np.ndarray, np.ndarray, Any, Any]:
        """
        Prepare data for LSTM training - FIXED VERSION
        
        Args:
            data: DataFrame with price and indicator data
            target_column: Column name for prediction target
            feature_columns: List of feature column names
            
        Returns:
            Tuple of (X, y, target_scaler, feature_scaler)
        """
        if feature_columns is None:
            # انتخاب ستون‌هایی که حتماً وجود دارند
            available_features = []
            potential_features = [
                'close_price', 'volume', 'open_price', 'high_price', 'low_price',
                'rsi', 'sma_20', 'ema_12', 'macd', 'market_cap'
            ]
            
            for col in potential_features:
                if col in data.columns:
                    available_features.append(col)
            
            feature_columns = available_features[:self.n_features]  # حداکثر n_features ستون
            
            if len(feature_columns) < 2:
                # حداقل ستون‌های پایه
                feature_columns = ['close_price', 'volume'] if 'volume' in data.columns else ['close_price', 'open_price']
        
        # بررسی وجود ستون‌ها
        missing_cols = [col for col in feature_columns if col not in data.columns]
        if missing_cols:
            logger.warning(f"Missing columns {missing_cols}, removing from features")
            feature_columns = [col for col in feature_columns if col in data.columns]
        
        if not feature_columns:
            raise ValueError("No valid feature columns found")
        
        if target_column not in data.columns:
            raise ValueError(f"Target column '{target_column}' not found in data")
        
        # مرتب کردن بر اساس timestamp
        if 'timestamp' in data.columns:
            data = data.sort_values('timestamp').copy()
        
        # Handle missing values - استفاده از روش جدید pandas
        logger.info(f"Using feature columns: {feature_columns}")
        data_clean = data.copy()
        
        # جایگزین کردن fillna قدیمی با روش جدید pandas
        for col in feature_columns + [target_column]:
            if col in data_clean.columns:
                # Forward fill then backward fill
                data_clean[col] = data_clean[col].ffill().bfill()
        
        # حذف NaN های باقی مانده
        data_clean = data_clean.dropna(subset=feature_columns + [target_column])
        
        if len(data_clean) < self.sequence_length + 1:
            raise ValueError(f"Insufficient data after cleaning: {len(data_clean)} < {self.sequence_length + 1}")
        
        # Extract features and target
        features = data_clean[feature_columns].values
        target = data_clean[target_column].values.reshape(-1, 1)
        
        logger.info(f"Data shape before scaling: features {features.shape}, target {target.shape}")
        
        # FIXED: Initialize and fit scalers properly
        if self.feature_scaler is None:
            self.feature_scaler = RobustScaler()  # More robust to outliers
        
        if self.scaler is None:
            self.scaler = MinMaxScaler(feature_range=(0, 1))
        
        # Fit and transform features
        features_scaled = self.feature_scaler.fit_transform(features)
        
        # Fit and transform target
        target_scaled = self.scaler.fit_transform(target)
        
        # Update n_features based on actual features used
        self.n_features = features_scaled.shape[1]
        
        # Create sequences for LSTM
        X, y = self._create_sequences(features_scaled, target_scaled.flatten())
        
        logger.info(f"✅ Data prepared successfully: X shape {X.shape}, y shape {y.shape}")
        logger.info(f"✅ Scalers fitted: feature_scaler={self.feature_scaler is not None}, target_scaler={self.scaler is not None}")
        
        return X, y, self.scaler, self.feature_scaler
'''
                
                # جایگزین کردن method قدیمی با جدید
                content = content[:start_pos] + new_prepare_data + content[end_pos:]
                print("✅ اصلاح prepare_data method")
        
        # ذخیره فایل اصلاح شده
        with open(lstm_file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ فایل lstm_predictor.py اصلاح شد")
        return True
        
    except Exception as e:
        print(f"❌ خطا در اصلاح فایل: {e}")
        return False

def test_fix():
    """تست اصلاح انجام شده"""
    print("\n🧪 تست اصلاح...")
    
    try:
        # Import کلاس اصلاح شده
        from app.ml.models.lstm_predictor import LSTMPredictor
        
        # تست ایجاد instance
        lstm = LSTMPredictor(sequence_length=10, n_features=3)
        print("✅ LSTMPredictor instance ایجاد شد")
        
        # تست dummy data
        import pandas as pd
        import numpy as np
        
        test_data = pd.DataFrame({
            'timestamp': pd.date_range('2023-01-01', periods=50, freq='1H'),
            'close_price': np.random.uniform(45000, 55000, 50),
            'volume': np.random.uniform(1000, 10000, 50),
            'open_price': np.random.uniform(44000, 54000, 50)
        })
        
        # تست prepare_data
        X, y, target_scaler, feature_scaler = lstm.prepare_data(test_data)
        print(f"✅ prepare_data کار می‌کند: X shape {X.shape}, y shape {y.shape}")
        print(f"✅ Scalers fitted: target={target_scaler is not None}, feature={feature_scaler is not None}")
        
        return True
        
    except Exception as e:
        print(f"❌ تست ناموفق: {e}")
        return False

if __name__ == "__main__":
    print("🚀 شروع اصلاح مشکل MinMaxScaler")
    print("=" * 50)
    
    # اجرای اصلاح
    if apply_scaler_fix():
        # تست اصلاح
        if test_fix():
            print("\n🎉 اصلاح با موفقیت انجام شد!")
            print("\nحالا می‌توانید دوباره تست کنید:")
            print("python temp/test_complete_ml_pipeline.py")
        else:
            print("\n⚠️ اصلاح انجام شد اما تست ناموفق بود")
    else:
        print("\n❌ اصلاح ناموفق")