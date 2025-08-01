# Test data shape
import numpy as np
X = np.random.random((100, 30))  # 2D data
X_reshaped = X.reshape(X.shape[0], X.shape[1], 1)  # Convert to 3D
print(f"Original: {X.shape}, Reshaped: {X_reshaped.shape}")
# Should output: Original: (100, 30), Reshaped: (100, 30, 1)