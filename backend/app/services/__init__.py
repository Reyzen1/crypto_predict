# File: backend/app/services/__init__.py
# Services package initialization

from app.services.auth import auth_service

__all__ = [
    "auth_service"
]