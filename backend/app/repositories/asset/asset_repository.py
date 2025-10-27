# backend/app/repositories/asset/asset.py
# Repository for asset management

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func, text
from datetime import datetime, timedelta

from ..base_repository import BaseRepository
from app.models.asset import Asset


class AssetRepository(BaseRepository):
    """
    Repository for cryptocurrency asset management
    """
    
    def __init__(self, db: Session):
        super().__init__(Asset, db)
  
    def get_by_symbol(self, symbol: str) -> Optional[Asset]:
        """Get asset by symbol"""
        return self.db.query(Asset).filter(Asset.symbol == symbol).first()
    
    def get_by_ids(self, asset_ids: List[int]) -> List[Asset]:
        """Get multiple assets by IDs in a single query to avoid N+1 problem"""
        if not asset_ids:
            return []
        return self.db.query(Asset).filter(Asset.id.in_(asset_ids)).all()
    
    def get_active_assets(self) -> List[Asset]:
        """Get all active assets"""
        return self.db.query(Asset).filter(
            Asset.is_active == True
        ).order_by(Asset.symbol.asc()).all()
    
    def search_assets(self, query: str, limit: int = 20) -> List[Asset]:
        """Search assets by symbol or name"""
        return self.db.query(Asset).filter(
            or_(
                Asset.symbol.ilike(f'%{query}%'),
                Asset.name.ilike(f'%{query}%')
            )
        ).limit(limit).all()
    
    def get_by_category(self, category: str) -> List[Asset]:
        """Get assets by category"""
        return self.db.query(Asset).filter(
            Asset.category == category,
            Asset.is_active == True
        ).order_by(Asset.symbol.asc()).all()
    
    def get_top_by_market_cap(self, limit: int = 100) -> List[Asset]:
        """Get top assets by market cap"""
        return self.db.query(Asset).filter(
            Asset.is_active == True,
            Asset.market_cap.isnot(None)
        ).order_by(Asset.market_cap.desc()).limit(limit).all()
    
    def get_assets_needing_update(self, hours: int = 24) -> List[Asset]:
        """Get assets that haven't been updated recently"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return self.db.query(Asset).filter(
            Asset.is_active == True,
            or_(
                Asset.last_updated < cutoff_time,
                Asset.last_updated.is_(None)
            )
        ).all()
    
    def update_market_data(self, asset_id: int, market_data: Dict[str, Any]) -> bool:
        """Update asset market data"""
        asset = self.get(asset_id)
        if not asset:
            return False
        
        if 'market_cap' in market_data:
            asset.market_cap = market_data['market_cap']
        if 'total_supply' in market_data:
            asset.total_supply = market_data['total_supply']
        if 'circulating_supply' in market_data:
            asset.circulating_supply = market_data['circulating_supply']
        
        asset.last_updated = datetime.utcnow()
        self.db.commit()
        return True
    
    def get_asset_statistics(self) -> Dict[str, Any]:
        """Get comprehensive asset statistics"""
        total_assets = self.db.query(func.count(Asset.id)).scalar()
        active_assets = self.db.query(func.count(Asset.id)).filter(
            Asset.is_active == True
        ).scalar()
        
        with_market_cap = self.db.query(func.count(Asset.id)).filter(
            Asset.market_cap.isnot(None),
            Asset.is_active == True
        ).scalar()
        
        total_market_cap = self.db.query(func.sum(Asset.market_cap)).filter(
            Asset.is_active == True
        ).scalar()
        
        return {
            'total_assets': total_assets or 0,
            'active_assets': active_assets or 0,
            'inactive_assets': (total_assets or 0) - (active_assets or 0),
            'assets_with_market_cap': with_market_cap or 0,
            'total_market_cap': float(total_market_cap) if total_market_cap else 0,
            'coverage_rate': (with_market_cap / active_assets * 100) if active_assets > 0 else 0
        }
    
    def activate_asset(self, asset_id: int) -> bool:
        """Activate an asset"""
        asset = self.get(asset_id)
        if not asset:
            return False
        
        asset.is_active = True
        asset.last_updated = datetime.utcnow()
        self.db.commit()
        return True
    
    def deactivate_asset(self, asset_id: int, reason: str = None) -> bool:
        """Deactivate an asset"""
        asset = self.get(asset_id)
        if not asset:
            return False
        
        asset.is_active = False
        asset.last_updated = datetime.utcnow()
        
        if reason:
            if not hasattr(asset, 'metadata') or not asset.metadata:
                asset.metadata = {}
            asset.metadata['deactivation_reason'] = reason
            asset.metadata['deactivated_at'] = datetime.utcnow().isoformat()
        
        self.db.commit()
        return True
    
    def bulk_update_market_data(self, updates: List[Dict[str, Any]]) -> Dict[str, int]:
        """Bulk update market data for multiple assets"""
        updated = 0
        failed = 0
        
        for update in updates:
            try:
                asset_id = update.get('asset_id')
                if not asset_id:
                    asset = self.get_by_symbol(update.get('symbol', ''))
                    asset_id = asset.id if asset else None
                
                if asset_id and self.update_market_data(asset_id, update):
                    updated += 1
                else:
                    failed += 1
            except Exception:
                failed += 1
        
        return {'updated': updated, 'failed': failed}
    
    def get_stale_assets(self, hours: int = 6) -> List[Asset]:
        """Get assets with stale market data"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return self.db.query(Asset).filter(
            Asset.is_active == True,
            or_(
                Asset.last_updated < cutoff_time,
                Asset.last_updated.is_(None)
            )
        ).order_by(Asset.market_cap.desc().nullslast()).all()
    
    def get_trending_assets(self, limit: int = 10) -> List[Asset]:
        """Get trending assets (placeholder - would need price change data)"""
        # This would typically join with price data to calculate trends
        # For now, return top assets by market cap as proxy
        return self.get_top_by_market_cap(limit)
    
    def validate_asset_data(self, asset_id: int) -> Dict[str, Any]:
        """Validate asset data completeness and consistency"""
        asset = self.get(asset_id)
        if not asset:
            return {'valid': False, 'error': 'Asset not found'}
        
        issues = []
        
        # Check required fields
        if not asset.symbol:
            issues.append('Missing symbol')
        if not asset.name:
            issues.append('Missing name')
        
        # Check data consistency
        if asset.circulating_supply and asset.total_supply:
            if asset.circulating_supply > asset.total_supply:
                issues.append('Circulating supply exceeds total supply')
        
        # Check market data freshness
        if asset.last_updated:
            hours_old = (datetime.utcnow() - asset.last_updated).total_seconds() / 3600
            if hours_old > 24:
                issues.append(f'Market data is {hours_old:.1f} hours old')
        else:
            issues.append('No market data update timestamp')
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'last_updated': asset.last_updated.isoformat() if asset.last_updated else None
        }