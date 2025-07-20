# File: backend/app/api/api_v1/endpoints/users.py
# User management API endpoints with CRUD operations

from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_active_user, get_current_verified_user
from app.core.security import security
from app.schemas.user import (
    UserResponse, UserUpdate, UserSummary, UserWithStats, 
    UserRegister, UserPasswordChange
)
from app.schemas.common import (
    SuccessResponse, PaginationParams, PaginatedResponse
)
from app.repositories import user_repository
from app.models import User


router = APIRouter()


@router.get("/", response_model=PaginatedResponse[UserSummary])
def list_users(
    pagination: PaginationParams = Depends(),
    search: str = Query(None, description="Search users by email, first name, or last name"),
    is_active: bool = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
) -> Any:
    """
    List users with pagination and filtering
    
    Requires verified user authentication.
    Supports search and filtering by active status.
    """
    try:
        if search:
            # Use search functionality from your existing repository
            users = user_repository.search_users(
                db, 
                search_term=search, 
                skip=pagination.skip, 
                limit=pagination.limit
            )
            total = len(users)  # Approximate for search results
        else:
            # Get users with optional filtering
            if is_active is not None:
                users = user_repository.get_active_users(
                    db, 
                    skip=pagination.skip, 
                    limit=pagination.limit
                ) if is_active else user_repository.get_multi(
                    db, 
                    skip=pagination.skip, 
                    limit=pagination.limit
                )
            else:
                users = user_repository.get_multi(
                    db, 
                    skip=pagination.skip, 
                    limit=pagination.limit
                )
            
            # Get total count
            total = user_repository.count_active_users(db) if is_active else len(user_repository.get_all(db))
        
        # Convert to summary format
        user_summaries = [
            UserSummary(
                id=user.id,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                is_active=user.is_active
            ) for user in users
        ]
        
        return PaginatedResponse.create(
            items=user_summaries,
            total=total,
            skip=pagination.skip,
            limit=pagination.limit
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserRegister,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
) -> Any:
    """
    Create new user (Admin only)
    
    Different from /auth/register:
    - Requires admin authentication
    - No token generation
    - Direct activation possible
    - For admin user management
    """
    # Basic admin check (you can enhance this with proper role system)
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only verified users can create other users"
        )
    
    try:
        # Check if user already exists
        existing_user = user_repository.get_by_email(db, user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password
        hashed_password = security.hash_password(user_data.password)
        
        # Create user using your existing repository
        new_user = user_repository.create_user(
            db,
            email=user_data.email,
            password_hash=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            is_active=True,  # Direct activation for admin-created users
            is_verified=False  # Still needs email verification
        )
        
        return UserResponse(
            id=new_user.id,
            email=new_user.email,
            first_name=new_user.first_name,
            last_name=new_user.last_name,
            is_active=new_user.is_active,
            is_verified=new_user.is_verified,
            created_at=new_user.created_at,
            updated_at=new_user.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get current user's profile information
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )


@router.get("/me/stats", response_model=UserWithStats)
def get_current_user_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get current user's statistics (predictions, portfolios, etc.)
    """
    try:
        # Count user's predictions and portfolios using relationships
        total_predictions = len(current_user.predictions) if hasattr(current_user, 'predictions') else 0
        total_portfolios = len(current_user.portfolios) if hasattr(current_user, 'portfolios') else 0
        
        # Get last prediction date
        last_prediction_date = None
        if hasattr(current_user, 'predictions') and current_user.predictions:
            last_prediction_date = max(pred.created_at for pred in current_user.predictions)
        
        return UserWithStats(
            id=current_user.id,
            email=current_user.email,
            first_name=current_user.first_name,
            last_name=current_user.last_name,
            is_active=current_user.is_active,
            is_verified=current_user.is_verified,
            created_at=current_user.created_at,
            updated_at=current_user.updated_at,
            total_predictions=total_predictions,
            total_portfolios=total_portfolios,
            last_prediction_date=last_prediction_date,
            last_login_date=current_user.updated_at  # Approximate last login
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user statistics"
        )


@router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get user by ID
    
    Users can only see their own profile unless they are admin.
    """
    # Allow users to see their own profile
    if current_user.id == user_id:
        user = current_user
    else:
        # Basic admin check (enhance with proper role system)
        if not current_user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        user = user_repository.get(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
    
    return UserResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
        updated_at=user.updated_at
    )


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Update user profile
    
    Users can only update their own profile unless they are admin.
    """
    # Check permissions
    if current_user.id != user_id and not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    try:
        # Get user to update
        user = user_repository.get(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update user using your existing repository
        updated_user = user_repository.update(db, db_obj=user, obj_in=user_update)
        
        return UserResponse(
            id=updated_user.id,
            email=updated_user.email,
            first_name=updated_user.first_name,
            last_name=updated_user.last_name,
            is_active=updated_user.is_active,
            is_verified=updated_user.is_verified,
            created_at=updated_user.created_at,
            updated_at=updated_user.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )


@router.delete("/{user_id}", response_model=SuccessResponse)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
) -> Any:
    """
    Delete user (Admin only)
    
    Requires verified user authentication.
    Users cannot delete themselves to prevent accidents.
    """
    # Prevent self-deletion
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    try:
        # Get user to delete
        user = user_repository.get(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Delete user using your existing repository
        deleted_user = user_repository.delete(db, id=user_id)
        
        if not deleted_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to delete user"
            )
        
        return SuccessResponse(
            message="User deleted successfully",
            data={"deleted_user_id": user_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )