"""
Moodle User Management API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from loguru import logger

from app.schemas.moodle_schemas import (
    MoodleUserCreate,
    MoodleUserUpdate,
    MoodleUserResponse,
    MoodleSearchCriteria
)
from app.adapters.moodle_adapter import MoodleAdapter
from app.core.dependencies import get_current_tenant_user, get_moodle_adapter

router = APIRouter()


@router.post("/users", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: MoodleUserCreate,
    adapter: MoodleAdapter = Depends(get_moodle_adapter),
    current_user = Depends(get_current_tenant_user)
):
    """
    Create a new Moodle user

    Requires:
    - User management permissions in Moodle
    """
    try:
        user_id = await adapter.create("users", user.dict())
        return {
            "success": True,
            "id": user_id,
            "message": "User created successfully"
        }
    except Exception as e:
        logger.error(f"Failed to create Moodle user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create user: {str(e)}"
        )


@router.get("/users", response_model=List[dict])
async def get_users(
    username: Optional[str] = None,
    email: Optional[str] = None,
    adapter: MoodleAdapter = Depends(get_moodle_adapter),
    current_user = Depends(get_current_tenant_user)
):
    """
    Get Moodle users

    Args:
        username: Filter by username
        email: Filter by email
    """
    try:
        criteria = []
        if username:
            criteria.append({"key": "username", "value": username})
        if email:
            criteria.append({"key": "email", "value": email})

        users = await adapter.get_users(criteria if criteria else None)
        return users
    except Exception as e:
        logger.error(f"Failed to get Moodle users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get users: {str(e)}"
        )


@router.get("/users/{user_id}", response_model=dict)
async def get_user(
    user_id: int,
    adapter: MoodleAdapter = Depends(get_moodle_adapter),
    current_user = Depends(get_current_tenant_user)
):
    """Get specific Moodle user by ID"""
    try:
        criteria = [{"key": "id", "value": str(user_id)}]
        users = await adapter.get_users(criteria)
        if not users:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )
        return users[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get Moodle user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get user: {str(e)}"
        )


@router.put("/users/{user_id}", response_model=dict)
async def update_user(
    user_id: int,
    user: MoodleUserUpdate,
    adapter: MoodleAdapter = Depends(get_moodle_adapter),
    current_user = Depends(get_current_tenant_user)
):
    """Update Moodle user"""
    try:
        user_data = user.dict(exclude_unset=True)
        user_data["id"] = user_id
        success = await adapter.write("users", user_id, user_data)
        return {
            "success": success,
            "message": "User updated successfully"
        }
    except Exception as e:
        logger.error(f"Failed to update Moodle user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update user: {str(e)}"
        )


@router.delete("/users/{user_id}", response_model=dict)
async def delete_user(
    user_id: int,
    adapter: MoodleAdapter = Depends(get_moodle_adapter),
    current_user = Depends(get_current_tenant_user)
):
    """Delete Moodle user"""
    try:
        success = await adapter.unlink("users", [user_id])
        return {
            "success": success,
            "message": "User deleted successfully"
        }
    except Exception as e:
        logger.error(f"Failed to delete Moodle user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete user: {str(e)}"
        )
