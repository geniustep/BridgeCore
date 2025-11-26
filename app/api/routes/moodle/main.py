"""
Main Moodle API Router
"""
from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger

from app.api.routes.moodle import courses, users
from app.adapters.moodle_adapter import MoodleAdapter
from app.core.dependencies import get_current_tenant_user, get_moodle_adapter
from app.schemas.moodle_schemas import MoodleSiteInfo

# Create main Moodle router
router = APIRouter(prefix="/moodle", tags=["moodle"])

# Include sub-routers
router.include_router(courses.router, prefix="", tags=["moodle-courses"])
router.include_router(users.router, prefix="", tags=["moodle-users"])


@router.get("/site-info", response_model=dict)
async def get_site_info(
    adapter: MoodleAdapter = Depends(get_moodle_adapter),
    current_user = Depends(get_current_tenant_user)
):
    """
    Get Moodle site information

    Returns site details, Moodle version, user info, etc.
    """
    try:
        site_info = await adapter.get_metadata("site")
        return site_info
    except Exception as e:
        logger.error(f"Failed to get Moodle site info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get site info: {str(e)}"
        )


@router.get("/health", response_model=dict)
async def check_connection(
    adapter: MoodleAdapter = Depends(get_moodle_adapter),
    current_user = Depends(get_current_tenant_user)
):
    """
    Check Moodle connection health

    Returns connection status and latency
    """
    import time
    try:
        start_time = time.time()
        is_connected = await adapter.check_connection()
        latency = (time.time() - start_time) * 1000  # ms

        return {
            "status": "connected" if is_connected else "disconnected",
            "latency_ms": round(latency, 2),
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Moodle connection check failed: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": time.time()
        }


@router.post("/call", response_model=dict)
async def call_function(
    function_name: str,
    params: dict = {},
    adapter: MoodleAdapter = Depends(get_moodle_adapter),
    current_user = Depends(get_current_tenant_user)
):
    """
    Call any Moodle Web Service function

    Args:
        function_name: Moodle function name (e.g., "core_course_get_courses")
        params: Function parameters

    This is a generic endpoint for calling any Moodle function
    """
    try:
        result = await adapter.call_method("", function_name, kwargs=params)
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        logger.error(f"Moodle function call failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Function call failed: {str(e)}"
        )
