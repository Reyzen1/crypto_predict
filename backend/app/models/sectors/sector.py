# File: backend\app\models\sectors\sector.py
# SQLAlchemy model for sector data

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, DECIMAL, ForeignKey, JSON, Index, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base

class CryptoSector(Base):
    """
    Cryptocurrency sector definitions
    """
    __tablename__ = "crypto_sectors"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Sector identification
    name = Column(String(50), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # Sector characteristics
    characteristics = Column(JSON, default=dict)
    sector_type = Column(String(20), default='general')
    maturity_level = Column(String(10), default='medium')
    risk_category = Column(String(10), default='medium')
    
    # Status and ordering
    is_active = Column(Boolean, default=True, index=True)
    sort_order = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    cryptocurrencies = relationship("Cryptocurrency", back_populates="sector")
    sector_mappings = relationship("CryptoSectorMapping", back_populates="sector")
    performance_records = relationship("SectorPerformance", back_populates="sector")
    
    def __repr__(self):
        return f"<CryptoSector(id={self.id}, name={self.name})>"

class CryptoSectorMapping(Base):
    """
    Many-to-many mapping between cryptocurrencies and sectors
    """
    __tablename__ = "crypto_sector_mapping"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # References
    crypto_id = Column(Integer, ForeignKey("cryptocurrencies.id"), nullable=False, index=True)
    sector_id = Column(Integer, ForeignKey("crypto_sectors.id"), nullable=False, index=True)
    
    # Mapping details
    allocation_percentage = Column(DECIMAL(5, 2), nullable=False, default=100)
    is_primary_sector = Column(Boolean, default=True)
    mapping_confidence = Column(DECIMAL(5, 4), default=1.0)
    mapping_source = Column(String(50), default='manual')
    sector_weight = Column(DECIMAL(5, 4), default=1.0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    cryptocurrency = relationship("Cryptocurrency", back_populates="sector_mappings")
    sector = relationship("CryptoSector", back_populates="sector_mappings")
    
    def __repr__(self):
        return f"<CryptoSectorMapping(crypto_id={self.crypto_id}, sector_id={self.sector_id})>"

# Constraints and indexes
UniqueConstraint('crypto_id', 'sector_id', name='crypto_sector_mapping_crypto_id_sector_id_key')
Index('idx_crypto_sector_crypto', CryptoSectorMapping.crypto_id, CryptoSectorMapping.is_primary_sector.desc())
Index('idx_crypto_sector_sector', CryptoSectorMapping.sector_id, CryptoSectorMapping.allocation_percentage.desc())
Index('idx_crypto_sector_primary', CryptoSectorMapping.is_primary_sector, CryptoSectorMapping.mapping_confidence.desc())
