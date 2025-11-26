"""
Moodle Course Management API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from loguru import logger

from app.schemas.moodle_schemas import (
    MoodleCourseCreate,
    MoodleCourseUpdate,
    MoodleCourseResponse
)
from app.adapters.moodle_adapter import MoodleAdapter
from app.core.dependencies import get_current_tenant_user, get_moodle_adapter

router = APIRouter()


@router.post("/courses", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_course(
    course: MoodleCourseCreate,
    adapter: MoodleAdapter = Depends(get_moodle_adapter),
    current_user = Depends(get_current_tenant_user)
):
    """
    Create a new Moodle course

    Requires:
    - Course management permissions in Moodle
    """
    try:
        course_id = await adapter.create("courses", course.dict())
        return {
            "success": True,
            "id": course_id,
            "message": "Course created successfully"
        }
    except Exception as e:
        logger.error(f"Failed to create Moodle course: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create course: {str(e)}"
        )


@router.get("/courses", response_model=List[dict])
async def get_courses(
    course_ids: Optional[str] = None,
    adapter: MoodleAdapter = Depends(get_moodle_adapter),
    current_user = Depends(get_current_tenant_user)
):
    """
    Get Moodle courses

    Args:
        course_ids: Comma-separated course IDs (optional, returns all if not provided)
    """
    try:
        ids = [int(id.strip()) for id in course_ids.split(",")] if course_ids else None
        courses = await adapter.get_courses(ids)
        return courses
    except Exception as e:
        logger.error(f"Failed to get Moodle courses: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get courses: {str(e)}"
        )


@router.get("/courses/{course_id}", response_model=dict)
async def get_course(
    course_id: int,
    adapter: MoodleAdapter = Depends(get_moodle_adapter),
    current_user = Depends(get_current_tenant_user)
):
    """Get specific Moodle course by ID"""
    try:
        courses = await adapter.get_courses([course_id])
        if not courses:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course {course_id} not found"
            )
        return courses[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get Moodle course: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get course: {str(e)}"
        )


@router.put("/courses/{course_id}", response_model=dict)
async def update_course(
    course_id: int,
    course: MoodleCourseUpdate,
    adapter: MoodleAdapter = Depends(get_moodle_adapter),
    current_user = Depends(get_current_tenant_user)
):
    """Update Moodle course"""
    try:
        course_data = course.dict(exclude_unset=True)
        course_data["id"] = course_id
        success = await adapter.write("courses", course_id, course_data)
        return {
            "success": success,
            "message": "Course updated successfully"
        }
    except Exception as e:
        logger.error(f"Failed to update Moodle course: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update course: {str(e)}"
        )


@router.delete("/courses/{course_id}", response_model=dict)
async def delete_course(
    course_id: int,
    adapter: MoodleAdapter = Depends(get_moodle_adapter),
    current_user = Depends(get_current_tenant_user)
):
    """Delete Moodle course"""
    try:
        success = await adapter.unlink("courses", [course_id])
        return {
            "success": success,
            "message": "Course deleted successfully"
        }
    except Exception as e:
        logger.error(f"Failed to delete Moodle course: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete course: {str(e)}"
        )


@router.get("/courses/{course_id}/users", response_model=List[dict])
async def get_enrolled_users(
    course_id: int,
    adapter: MoodleAdapter = Depends(get_moodle_adapter),
    current_user = Depends(get_current_tenant_user)
):
    """Get users enrolled in a course"""
    try:
        users = await adapter.get_enrolled_users(course_id)
        return users
    except Exception as e:
        logger.error(f"Failed to get enrolled users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get enrolled users: {str(e)}"
        )


@router.post("/courses/{course_id}/enrol", response_model=dict)
async def enrol_user(
    course_id: int,
    user_id: int,
    role_id: int = 5,  # Default: student
    adapter: MoodleAdapter = Depends(get_moodle_adapter),
    current_user = Depends(get_current_tenant_user)
):
    """
    Enrol user in course

    Args:
        course_id: Course ID
        user_id: User ID
        role_id: Role ID (5=student, 3=teacher, 4=non-editing teacher)
    """
    try:
        success = await adapter.enrol_user(course_id, user_id, role_id)
        return {
            "success": success,
            "message": f"User {user_id} enrolled in course {course_id}"
        }
    except Exception as e:
        logger.error(f"Failed to enrol user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to enrol user: {str(e)}"
        )
