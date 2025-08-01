# File: backend/app/ml/config/persistent_registry.py
# Persistent Model Registry - Complete implementation for auto-loading models

import os
import json
import glob
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import numpy as np
from decimal import Decimal


logger = logging.getLogger(__name__)


class MLJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for ML registry data"""
    
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)
    
class PersistentModelRegistry:
    """
    Model Registry with persistence support
    Automatically loads existing models on startup and saves changes to disk
    """
    
    def __init__(self, models_dir: str = "models"):
        self.models: Dict[str, Dict[str, Any]] = {}
        self.active_models: Dict[str, str] = {}
        self.models_dir = models_dir
        self.registry_file = os.path.join(models_dir, "registry.json")
        
        # Create models directory if it doesn't exist
        os.makedirs(models_dir, exist_ok=True)
        
        # Auto-load existing models on initialization
        self._load_existing_models()
        
        logger.info(f"✅ PersistentModelRegistry initialized with {len(self.models)} models")
    
    def _load_existing_models(self) -> None:
        """
        Load existing models from files and registry
        Called automatically on startup
        """
        logger.info("🔄 Loading existing models on startup...")
        
        # Step 1: Try to load from registry file
        loaded_from_registry = self._load_from_registry_file()
        
        # Step 2: Scan for model files not in registry
        scanned_count = self._scan_and_register_model_files()
        
        # Step 3: Validate and clean up
        self._validate_registered_models()
        
        # Step 4: Ensure active models
        self._ensure_active_models()
        
        total_models = len(self.models)
        logger.info(f"✅ Startup complete: {total_models} models loaded")
        logger.info(f"   From registry file: {loaded_from_registry}")
        logger.info(f"   From file scanning: {scanned_count}")
        
        # Save current state (in case we found new models)
        if scanned_count > 0:
            self.save_registry()
    
    def _load_from_registry_file(self) -> int:
        """Load models from saved registry file"""
        if not os.path.exists(self.registry_file):
            logger.info("📝 No existing registry file found")
            return 0
        
        try:
            with open(self.registry_file, 'r') as f:
                data = json.load(f)
            
            self.models = data.get('models', {})
            self.active_models = data.get('active_models', {})
            
            loaded_count = len(self.models)
            logger.info(f"📂 Loaded {loaded_count} models from registry file")
            return loaded_count
            
        except Exception as e:
            logger.error(f"❌ Failed to load registry file: {str(e)}")
            # Reset to empty state if file is corrupted
            self.models = {}
            self.active_models = {}
            return 0
    
    def _scan_and_register_model_files(self) -> int:
        """Scan for model files and register missing ones"""
        if not os.path.exists(self.models_dir):
            logger.info(f"📁 Models directory doesn't exist: {self.models_dir}")
            return 0
        
        # Find all model files
        model_patterns = ["*.h5", "*.pkl", "*.joblib", "*.pt", "*.keras"]
        model_files = []
        
        for pattern in model_patterns:
            model_files.extend(glob.glob(os.path.join(self.models_dir, pattern)))
        
        if not model_files:
            logger.info("📋 No model files found in directory")
            return 0
        
        logger.info(f"📂 Found {len(model_files)} model files")
        
        registered_count = 0
        
        for model_file in model_files:
            try:
                filename = os.path.basename(model_file)
                model_id = os.path.splitext(filename)[0]
                
                # Skip if already registered
                if model_id in self.models:
                    logger.debug(f"⏭️ Skipping already registered: {model_id}")
                    continue
                
                # Extract crypto symbol from filename
                crypto_symbol = self._extract_crypto_symbol(filename)
                if not crypto_symbol:
                    logger.warning(f"⚠️ Cannot determine crypto symbol for {filename}")
                    crypto_symbol = "UNKNOWN"
                
                # Register the model
                self._register_scanned_model(
                    model_id=model_id,
                    model_file=model_file,
                    crypto_symbol=crypto_symbol
                )
                registered_count += 1
                logger.info(f"📝 Auto-registered: {model_id} ({crypto_symbol})")
                
            except Exception as e:
                logger.error(f"❌ Failed to register {filename}: {str(e)}")
                continue
        
        return registered_count
    
    def _extract_crypto_symbol(self, filename: str) -> Optional[str]:
        """Extract cryptocurrency symbol from filename"""
        filename_lower = filename.lower()
        
        # Common cryptocurrency patterns
        crypto_patterns = {
            'btc': 'BTC', 'bitcoin': 'BTC',
            'eth': 'ETH', 'ethereum': 'ETH', 
            'ada': 'ADA', 'cardano': 'ADA',
            'bnb': 'BNB', 'binance': 'BNB',
            'sol': 'SOL', 'solana': 'SOL',
            'dot': 'DOT', 'polkadot': 'DOT',
            'avax': 'AVAX', 'avalanche': 'AVAX'
        }
        
        # Check for known patterns
        for pattern, symbol in crypto_patterns.items():
            if pattern in filename_lower:
                return symbol
        
        # Try to extract from pattern like "symbol_model_date.h5"
        parts = filename_lower.split('_')
        if len(parts) > 0:
            potential_symbol = parts[0].upper()
            # Check if it looks like a valid crypto symbol (2-5 characters)
            if 2 <= len(potential_symbol) <= 5 and potential_symbol.isalpha():
                return potential_symbol
        
        return None
    
    def _register_scanned_model(self, model_id: str, model_file: str, crypto_symbol: str) -> None:
        """Register a model found during scanning"""
        try:
            file_stats = os.stat(model_file)
            file_size_mb = round(file_stats.st_size / (1024*1024), 2)
            
            model_data = {
                'model_id': model_id,
                'crypto_symbol': crypto_symbol,
                'model_type': 'lstm',  # Default assumption
                'model_path': model_file,
                'performance_metrics': {
                    'auto_discovered': True,
                    'file_size_mb': file_size_mb,
                    'discovery_method': 'file_scan'
                },
                'metadata': {
                    'discovered_at': datetime.now().isoformat(),
                    'file_modified': datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                    'auto_registered': True,
                    'registration_source': 'startup_scan'
                },
                'registered_at': datetime.now().isoformat(),
                'is_active': False
            }
            
            self.models[model_id] = model_data
            
        except Exception as e:
            logger.error(f"❌ Error registering scanned model {model_id}: {str(e)}")
            raise
    
    def _validate_registered_models(self) -> None:
        """Validate that registered models still exist and clean up invalid ones"""
        invalid_models = []
        
        for model_id, model_data in self.models.items():
            model_path = model_data.get('model_path')
            if not model_path or not os.path.exists(model_path):
                invalid_models.append(model_id)
                logger.warning(f"⚠️ Model file missing: {model_id} -> {model_path}")
        
        # Remove invalid models
        for model_id in invalid_models:
            del self.models[model_id]
            
            # Also remove from active models
            for crypto_symbol, active_id in list(self.active_models.items()):
                if active_id == model_id:
                    del self.active_models[crypto_symbol]
                    logger.info(f"🧹 Removed inactive model for {crypto_symbol}: {model_id}")
        
        if invalid_models:
            logger.info(f"🧹 Cleaned up {len(invalid_models)} invalid model references")
            self.save_registry()
            logger.info(f"💾 Registry updated - now has {len(self.models)} valid models")
    
    def _ensure_active_models(self) -> None:
        """Ensure each crypto has an active model if possible"""
        crypto_models = {}
        
        # Group models by crypto symbol
        for model_id, model_data in self.models.items():
            crypto_symbol = model_data.get('crypto_symbol', 'UNKNOWN')
            if crypto_symbol not in crypto_models:
                crypto_models[crypto_symbol] = []
            crypto_models[crypto_symbol].append((model_id, model_data))
        
        # Set active models for cryptos that don't have one
        for crypto_symbol, models_list in crypto_models.items():
            if crypto_symbol not in self.active_models and models_list:
                # Choose the most recent model based on registration time
                try:
                    latest_model = max(
                        models_list, 
                        key=lambda x: x[1].get('registered_at', '1970-01-01T00:00:00')
                    )
                    model_id = latest_model[0]
                    
                    self.active_models[crypto_symbol] = model_id
                    self.models[model_id]['is_active'] = True
                    
                    logger.info(f"🎯 Set active model for {crypto_symbol}: {model_id}")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to set active model for {crypto_symbol}: {str(e)}")
    
    def save_registry(self) -> bool:
        """Save current registry state to file with improved error handling"""
        try:
            os.makedirs(os.path.dirname(self.registry_file), exist_ok=True)
            
            data = {
                'models': self.models,
                'active_models': self.active_models,
                'last_updated': datetime.utcnow().isoformat(),
                'version': '1.0'
            }
            
            with open(self.registry_file, 'w') as f:
                json.dump(data, f, cls=MLJSONEncoder, indent=2)  # Using custom encoder
            
            logger.info(f"✅ Registry saved successfully: {len(self.models)} models")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save registry: {str(e)}")
            return False
    
    # Standard ModelRegistry interface methods
    def register_model(self, model_id: str, crypto_symbol: str, model_type: str, 
                      model_path: str, performance_metrics: Dict[str, Any], 
                      metadata: Optional[Dict[str, Any]] = None) -> None:
        """Register a new model and save to file"""
        try:
            self.models[model_id] = {
                'model_id': model_id,
                'crypto_symbol': crypto_symbol,
                'model_type': model_type,
                'model_path': model_path,
                'performance_metrics': performance_metrics or {},
                'metadata': metadata or {},
                'registered_at': datetime.now().isoformat(),
                'is_active': False
            }
            
            # Save to file immediately
            self.save_registry()
            logger.info(f"✅ Registered and saved model: {model_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to register model {model_id}: {str(e)}")
            raise
    
    def set_active_model(self, crypto_symbol: str, model_id: str) -> None:
        """Set active model and save state"""
        if model_id not in self.models:
            raise ValueError(f"Model {model_id} not found in registry")
        
        try:
            # Deactivate previous active model
            if crypto_symbol in self.active_models:
                old_model_id = self.active_models[crypto_symbol]
                if old_model_id in self.models:
                    self.models[old_model_id]['is_active'] = False
            
            # Activate new model
            self.active_models[crypto_symbol] = model_id
            self.models[model_id]['is_active'] = True
            
            # Save to file
            self.save_registry()
            logger.info(f"🎯 Set active model for {crypto_symbol}: {model_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to set active model: {str(e)}")
            raise
    
    def get_active_model(self, crypto_symbol: str) -> Optional[Dict[str, Any]]:
        """Get active model info"""
        if crypto_symbol not in self.active_models:
            return None
        
        model_id = self.active_models[crypto_symbol]
        return self.models.get(model_id)
    
    def list_models(self) -> List[Dict[str, Any]]:
        """List all registered models"""
        return list(self.models.values())
    
    def get_models_for_crypto(self, crypto_symbol: str) -> List[Dict[str, Any]]:
        """Get all models for a specific cryptocurrency"""
        return [
            model_data for model_data in self.models.values()
            if model_data.get('crypto_symbol') == crypto_symbol
        ]
    
    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get specific model information"""
        return self.models.get(model_id)
    
    def remove_model(self, model_id: str) -> bool:
        """Remove a model from registry"""
        if model_id not in self.models:
            return False
        
        try:
            # Remove from active models if needed
            model_data = self.models[model_id]
            crypto_symbol = model_data.get('crypto_symbol')
            
            if crypto_symbol and self.active_models.get(crypto_symbol) == model_id:
                del self.active_models[crypto_symbol]
            
            # Remove from models
            del self.models[model_id]
            
            # Save changes
            self.save_registry()
            logger.info(f"🗑️ Removed model: {model_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to remove model {model_id}: {str(e)}")
            return False


def create_persistent_model_registry(models_dir: str = "models") -> PersistentModelRegistry:
    """Factory function to create a persistent model registry instance"""
    return PersistentModelRegistry(models_dir)