# File: temp/test_persistent_registry.py
# Test script for Persistent Model Registry functionality

import sys
import os
import json
import shutil
from pathlib import Path
from datetime import datetime

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))


class PersistentRegistryTester:
    """Test the persistent model registry functionality"""
    
    def __init__(self):
        self.test_models_dir = "test_models"
        self.backup_models_dir = "models_backup"
        
    def print_section(self, title: str):
        """Print a formatted section header"""
        print(f"\n{'='*60}")
        print(f"🧪 {title}")
        print(f"{'='*60}")
    
    def print_result(self, success: bool, message: str, details: str = None):
        """Print test result"""
        icon = "✅" if success else "❌"
        print(f"{icon} {message}")
        if details:
            print(f"   Details: {details}")
    
    def setup_test_environment(self) -> bool:
        """Set up test environment with sample model files"""
        self.print_section("Setting Up Test Environment")
        
        try:
            # Backup existing models directory if it exists
            if os.path.exists("models"):
                if os.path.exists(self.backup_models_dir):
                    shutil.rmtree(self.backup_models_dir)
                shutil.move("models", self.backup_models_dir)
                self.print_result(True, "Backed up existing models directory")
            
            # Create test models directory
            os.makedirs(self.test_models_dir, exist_ok=True)
            
            # Create sample model files
            test_models = [
                "btc_lstm_20250729_143022.h5",
                "btc_lstm_20250729_150045.h5", 
                "eth_lstm_20250729_144033.h5",
                "ada_lstm_20250729_145055.h5"
            ]
            
            for model_file in test_models:
                model_path = os.path.join(self.test_models_dir, model_file)
                # Create dummy model file with some content
                with open(model_path, 'wb') as f:
                    f.write(b"dummy_model_data_" + model_file.encode() * 100)
                
                self.print_result(True, f"Created test model: {model_file}")
            
            # Rename test directory to models
            if os.path.exists("models"):
                shutil.rmtree("models")
            shutil.move(self.test_models_dir, "models")
            
            self.print_result(True, "Test environment setup complete", 
                            f"Created {len(test_models)} test model files")
            return True
            
        except Exception as e:
            self.print_result(False, f"Failed to setup test environment: {str(e)}")
            return False
    
    def test_registry_initialization(self) -> bool:
        """Test registry initialization and auto-loading"""
        self.print_section("Testing Registry Initialization")
        
        try:
            # Import and create registry
            from app.ml.config.persistent_registry import create_persistent_model_registry
            
            registry = create_persistent_model_registry("models")
            
            # Check if models were auto-loaded
            total_models = len(registry.models)
            active_models = len(registry.active_models)
            
            self.print_result(True, f"Registry initialized successfully")
            self.print_result(True, f"Auto-loaded {total_models} models")
            self.print_result(True, f"Set {active_models} active models")
            
            # Display loaded models
            if registry.models:
                print("\n📋 Loaded Models:")
                for model_id, model_data in registry.models.items():
                    crypto = model_data.get('crypto_symbol', 'UNKNOWN')
                    is_active = model_data.get('is_active', False)
                    active_indicator = "🎯" if is_active else "  "
                    print(f"   {active_indicator} {model_id} ({crypto})")
            
            return total_models > 0
            
        except Exception as e:
            self.print_result(False, f"Registry initialization failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_registry_persistence(self) -> bool:
        """Test registry file saving and loading"""
        self.print_section("Testing Registry Persistence")
        
        try:
            from app.ml.config.persistent_registry import create_persistent_model_registry
            
            # Create first registry instance
            registry1 = create_persistent_model_registry("models")
            initial_count = len(registry1.models)
            
            # Add a new model manually
            test_model_id = "test_manual_model"
            registry1.register_model(
                model_id=test_model_id,
                crypto_symbol="TEST",
                model_type="lstm",
                model_path=os.path.join("models", "test_model.h5"),
                performance_metrics={"test": True},
                metadata={"manual_test": True}
            )
            
            self.print_result(True, f"Added manual test model: {test_model_id}")
            
            # Check if registry file was created
            registry_file = os.path.join("models", "registry.json")
            if os.path.exists(registry_file):
                self.print_result(True, "Registry file created successfully")
                
                # Check file content
                with open(registry_file, 'r') as f:
                    data = json.load(f)
                
                saved_models = len(data.get('models', {}))
                self.print_result(True, f"Registry file contains {saved_models} models")
            else:
                self.print_result(False, "Registry file not created")
                return False
            
            # Create second registry instance (simulating restart)
            registry2 = create_persistent_model_registry("models")
            loaded_count = len(registry2.models)
            
            # Check if the manual model was loaded
            if test_model_id in registry2.models:
                self.print_result(True, "Manual model persisted across restart")
            else:
                self.print_result(False, "Manual model not persisted")
                return False
            
            self.print_result(True, f"Persistence test passed", 
                            f"Models: {initial_count} → {loaded_count}")
            return True
            
        except Exception as e:
            self.print_result(False, f"Persistence test failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_active_model_management(self) -> bool:
        """Test active model setting and retrieval"""
        self.print_section("Testing Active Model Management")
        
        try:
            from app.ml.config.persistent_registry import create_persistent_model_registry
            
            registry = create_persistent_model_registry("models")
            
            # Test getting active model for BTC
            btc_active = registry.get_active_model("BTC")
            if btc_active:
                self.print_result(True, f"BTC active model: {btc_active.get('model_id')}")
            else:
                self.print_result(False, "No active BTC model found")
                return False
            
            # Test setting a different active model
            btc_models = registry.get_models_for_crypto("BTC")
            if len(btc_models) > 1:
                # Set the second model as active
                new_active_id = btc_models[1]['model_id']
                registry.set_active_model("BTC", new_active_id)
                
                # Verify the change
                updated_active = registry.get_active_model("BTC")
                if updated_active and updated_active['model_id'] == new_active_id:
                    self.print_result(True, f"Successfully changed active model to: {new_active_id}")
                else:
                    self.print_result(False, "Failed to change active model")
                    return False
            
            return True
            
        except Exception as e:
            self.print_result(False, f"Active model test failed: {str(e)}")
            return False
    
    def test_model_validation(self) -> bool:
        """Test model file validation and cleanup"""
        self.print_section("Testing Model Validation")
        
        try:
            from app.ml.config.persistent_registry import create_persistent_model_registry
            
            # Create registry
            registry = create_persistent_model_registry("models")
            initial_count = len(registry.models)
            
            # Add a model with non-existent file
            fake_model_id = "fake_model_test"
            registry.models[fake_model_id] = {
                'model_id': fake_model_id,
                'crypto_symbol': 'FAKE',
                'model_type': 'lstm',
                'model_path': 'non_existent_file.h5',
                'is_active': False
            }
            
            self.print_result(True, "Added fake model with non-existent file")
            
            # Create new registry instance to trigger validation
            registry2 = create_persistent_model_registry("models")
            final_count = len(registry2.models)
            
            # Check if fake model was removed
            if fake_model_id not in registry2.models:
                self.print_result(True, "Invalid model was cleaned up successfully")
            else:
                self.print_result(False, "Invalid model was not cleaned up")
                return False
            
            self.print_result(True, f"Validation test passed", 
                            f"Models: {initial_count+1} → {final_count}")
            return True
            
        except Exception as e:
            self.print_result(False, f"Validation test failed: {str(e)}")
            return False
    
    def cleanup_test_environment(self) -> bool:
        """Clean up test environment and restore original state"""
        self.print_section("Cleaning Up Test Environment")
        
        try:
            # Remove test models directory
            if os.path.exists("models"):
                shutil.rmtree("models")
                self.print_result(True, "Removed test models directory")
            
            # Restore original models directory if it existed
            if os.path.exists(self.backup_models_dir):
                shutil.move(self.backup_models_dir, "models")
                self.print_result(True, "Restored original models directory")
            
            return True
            
        except Exception as e:
            self.print_result(False, f"Cleanup failed: {str(e)}")
            return False
    
    def run_all_tests(self) -> bool:
        """Run all tests"""
        print("🚀 Starting Persistent Registry Tests")
        print(f"Timestamp: {datetime.now().isoformat()}")
        
        tests = [
            ("Setup", self.setup_test_environment),
            ("Initialization", self.test_registry_initialization),
            ("Persistence", self.test_registry_persistence),
            ("Active Model Management", self.test_active_model_management),
            ("Model Validation", self.test_model_validation),
            ("Cleanup", self.cleanup_test_environment)
        ]
        
        results = []
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ Test {test_name} crashed: {str(e)}")
                results.append((test_name, False))
        
        # Print summary
        self.print_section("Test Summary")
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            icon = "✅" if result else "❌"
            print(f"{icon} {test_name}")
        
        print(f"\n📊 Overall Result: {passed}/{total} tests passed")
        
        if passed == total:
            self.print_result(True, "All tests passed! 🎉")
            return True
        else:
            self.print_result(False, f"{total - passed} tests failed")
            return False


def main():
    """Run the tests"""
    tester = PersistentRegistryTester()
    success = tester.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())