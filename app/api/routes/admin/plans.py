"""
Admin plan management routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.db.session import get_db
from app.schemas.admin import PlanCreate, PlanUpdate, PlanResponse
from app.repositories.plan_repository import PlanRepository
from app.api.routes.admin.dependencies import get_current_admin
from app.models.admin import Admin

router = APIRouter(prefix="/admin/plans", tags=["Admin Plan Management"])


@router.get("", response_model=List[PlanResponse])
async def list_plans(
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    List all subscription plans

    **Requires:**
    - Valid admin JWT token

    **Returns:**
    - List of all plans
    """
    plan_repo = PlanRepository(db)
    plans = await plan_repo.get_multi(skip=0, limit=1000, order_by="price_monthly")
    return plans


@router.get("/{plan_id}", response_model=PlanResponse)
async def get_plan(
    plan_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    Get plan by ID

    **Requires:**
    - Valid admin JWT token

    **Returns:**
    - Plan details

    **Errors:**
    - 404: Plan not found
    """
    plan_repo = PlanRepository(db)
    plan = await plan_repo.get_by_id_uuid(plan_id)
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found"
        )
    
    return plan


@router.post("", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
async def create_plan(
    plan_data: PlanCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    Create a new subscription plan

    **Requires:**
    - Valid admin JWT token
    - Super admin role

    **Returns:**
    - Created plan
    """
    from app.models.plan import Plan
    import uuid
    
    plan_repo = PlanRepository(db)
    
    # Check if plan name already exists
    existing = await plan_repo.get_by_name(plan_data.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Plan name already exists"
        )
    
    # Create plan
    plan = Plan(
        id=uuid.uuid4(),
        **plan_data.dict()
    )
    
    plan_repo.session.add(plan)
    await plan_repo.session.commit()
    await plan_repo.session.refresh(plan)
    
    return plan


@router.put("/{plan_id}", response_model=PlanResponse)
async def update_plan(
    plan_id: UUID,
    plan_data: PlanUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    Update a subscription plan

    **Requires:**
    - Valid admin JWT token
    - Super admin role

    **Returns:**
    - Updated plan

    **Errors:**
    - 404: Plan not found
    """
    plan_repo = PlanRepository(db)
    plan = await plan_repo.get_by_id_uuid(plan_id)
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found"
        )
    
    # Update fields
    update_data = plan_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(plan, field, value)
    
    await plan_repo.session.commit()
    await plan_repo.session.refresh(plan)
    
    return plan


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan(
    plan_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    Delete a subscription plan (soft delete by setting is_active=False)

    **Requires:**
    - Valid admin JWT token
    - Super admin role

    **Errors:**
    - 404: Plan not found
    """
    plan_repo = PlanRepository(db)
    plan = await plan_repo.get_by_id_uuid(plan_id)
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found"
        )
    
    # Soft delete
    plan.is_active = False
    await plan_repo.session.commit()
    
    return None

