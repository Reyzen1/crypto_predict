# File: ./backend/app/repositories/base.py
# Base repository class with common CRUD operations

from typing import Type, TypeVar, Generic, List, Optional, Any, Dict
from sqlalchemy.orm import Session, DeclarativeBase
from sqlalchemy import and_, or_, desc, asc
from pydantic import BaseModel

# Type variables for generic repository
ModelType = TypeVar("ModelType", bound=DeclarativeBase)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base repository class providing common CRUD operations
    
    This implements the Repository Pattern to abstract database operations
    and provide a clean interface for data access
    """

    def __init__(self, model: Type[ModelType], db: Session):
        """
        Initialize repository with the model class and database session
        
        Args:
            model: SQLAlchemy model class
            db: Database session
        """
        self.model = model
        self.db = db

    def get(self, id: int) -> Optional[ModelType]:
        """
        Get a single record by ID
        
        Args:
            id: Primary key value
            
        Returns:
            Model instance or None if not found
        """
        return self.db.query(self.model).filter(self.model.id == id).first()

    def get_multi(
        self, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        order_by: str = "id",
        order_desc: bool = False
    ) -> List[ModelType]:
        """
        Get multiple records with pagination and ordering
        
        Args:
            skip: Number of records to skip (offset)
            limit: Maximum number of records to return
            order_by: Column name to order by
            order_desc: Whether to order in descending order
            
        Returns:
            List of model instances
        """
        query = self.db.query(self.model)
        
        # Apply ordering
        if hasattr(self.model, order_by):
            column = getattr(self.model, order_by)
            if order_desc:
                query = query.order_by(desc(column))
            else:
                query = query.order_by(asc(column))
        
        return query.offset(skip).limit(limit).all()

    def create(self, *, obj_in: CreateSchemaType) -> ModelType:
        """
        Create a new record
        
        Args:
            obj_in: Pydantic schema with data to create
            
        Returns:
            Created model instance
        """
        if isinstance(obj_in, dict):
            create_data = obj_in
        else:
            create_data = obj_in.model_dump(exclude_unset=True)
        
        db_obj = self.model(**create_data)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(
        self, 
        *, 
        db_obj: ModelType, 
        obj_in: UpdateSchemaType | Dict[str, Any]
    ) -> ModelType:
        """
        Update an existing record
        
        Args:
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
        
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update_no_obj_return(
        self, 
        *, 
        db_obj: ModelType, 
        obj_in: UpdateSchemaType | Dict[str, Any]
    ) -> None:
        """
        Update an existing record
        
        Args:
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
        
        self.db.add(db_obj)
        self.db.commit()
        return 

    def delete(self, *, id: int) -> Optional[ModelType]:
        """
        Delete a record by ID
        
        Args:
            id: Primary key value
            
        Returns:
            Deleted model instance or None if not found
        """
        obj = self.db.query(self.model).get(id)
        if obj:
            self.db.delete(obj)
            self.db.commit()
        return obj

    def get_by_field(
        self, 
        field_name: str, 
        field_value: Any
    ) -> Optional[ModelType]:
        """
        Get a single record by any field
        
        Args:
            field_name: Name of the field to filter by
            field_value: Value to filter for
            
        Returns:
            Model instance or None if not found
        """
        if hasattr(self.model, field_name):
            field = getattr(self.model, field_name)
            return self.db.query(self.model).filter(field == field_value).first()
        return None

    def count(self) -> int:
        """
        Get total count of records
        
        Returns:
            Total number of records
        """
        return self.db.query(self.model).count()

    def exists(self, id: int) -> bool:
        """
        Check if a record exists by ID
        
        Args:
            id: Primary key value
            
        Returns:
            True if record exists, False otherwise
        """
        return self.db.query(self.model).filter(self.model.id == id).first() is not None

    def get_by_filters(self, filters: Dict[str, Any], **kwargs) -> List[ModelType]:
        """
        Get records by multiple filters
        
        Args:
            filters: Dictionary of field names and values to filter by
            **kwargs: Additional query parameters (limit, skip, order_by, order_desc)
            
        Returns:
            List of model instances matching filters
        """
        query = self.db.query(self.model)
        
        # Apply filters
        for field_name, field_value in filters.items():
            if hasattr(self.model, field_name):
                field = getattr(self.model, field_name)
                query = query.filter(field == field_value)
        
        # Apply ordering if specified
        order_by = kwargs.get('order_by', 'id')
        order_desc = kwargs.get('order_desc', False)
        
        if hasattr(self.model, order_by):
            column = getattr(self.model, order_by)
            if order_desc:
                query = query.order_by(desc(column))
            else:
                query = query.order_by(asc(column))
        
        # Apply pagination if specified
        skip = kwargs.get('skip', 0)
        limit = kwargs.get('limit', None)
        
        if skip > 0:
            query = query.offset(skip)
        if limit:
            query = query.limit(limit)
        
        return query.all()
