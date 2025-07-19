# File: ./backend/app/repositories/base.py
# Base repository class with common CRUD operations

from typing import Type, TypeVar, Generic, List, Optional, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from pydantic import BaseModel

from app.core.database import Base

# Type variables for generic repository
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base repository class providing common CRUD operations
    
    This implements the Repository Pattern to abstract database operations
    and provide a clean interface for data access
    """

    def __init__(self, model: Type[ModelType]):
        """
        Initialize repository with the model class
        
        Args:
            model: SQLAlchemy model class
        """
        self.model = model

    def get(self, db: Session, id: int) -> Optional[ModelType]:
        """
        Get a single record by ID
        
        Args:
            db: Database session
            id: Primary key value
            
        Returns:
            Model instance or None if not found
        """
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        order_by: str = "id",
        order_desc: bool = False
    ) -> List[ModelType]:
        """
        Get multiple records with pagination and ordering
        
        Args:
            db: Database session
            skip: Number of records to skip (offset)
            limit: Maximum number of records to return
            order_by: Column name to order by
            order_desc: Whether to order in descending order
            
        Returns:
            List of model instances
        """
        query = db.query(self.model)
        
        # Apply ordering
        if hasattr(self.model, order_by):
            column = getattr(self.model, order_by)
            if order_desc:
                query = query.order_by(desc(column))
            else:
                query = query.order_by(asc(column))
        
        return query.offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """
        Create a new record
        
        Args:
            db: Database session
            obj_in: Pydantic schema with data to create
            
        Returns:
            Created model instance
        """
        if isinstance(obj_in, dict):
            create_data = obj_in
        else:
            create_data = obj_in.model_dump(exclude_unset=True)
        
        db_obj = self.model(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, 
        db: Session, 
        *, 
        db_obj: ModelType, 
        obj_in: UpdateSchemaType | Dict[str, Any]
    ) -> ModelType:
        """
        Update an existing record
        
        Args:
            db: Database session
            db_obj: Existing model instance to update
            obj_in: Pydantic schema or dict with update data
            
        Returns:
            Updated model instance
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, *, id: int) -> Optional[ModelType]:
        """
        Delete a record by ID
        
        Args:
            db: Database session
            id: Primary key value
            
        Returns:
            Deleted model instance or None if not found
        """
        obj = db.query(self.model).get(id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj

    def get_by_field(
        self, 
        db: Session, 
        field_name: str, 
        field_value: Any
    ) -> Optional[ModelType]:
        """
        Get a single record by any field
        
        Args:
            db: Database session
            field_name: Name of the field to filter by
            field_value: Value to filter for
            
        Returns:
            Model instance or None if not found
        """
        if hasattr(self.model, field_name):
            field = getattr(self.model, field_name)
            return db.query(self.model).filter(field == field_value).first()
        return None

    def count(self, db: Session) -> int:
        """
        Get total count of records
        
        Args:
            db: Database session
            
        Returns:
            Total number of records
        """
        return db.query(self.model).count()

    def exists(self, db: Session, id: int) -> bool:
        """
        Check if a record exists by ID
        
        Args:
            db: Database session
            id: Primary key value
            
        Returns:
            True if record exists, False otherwise
        """
        return db.query(self.model).filter(self.model.id == id).first() is not None
