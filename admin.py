from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Path, Query, status
from sqlalchemy.orm import Session
from app.models.base import get_db
from app.schemas.schemas import (
    SubscriptionPlanCreate, SubscriptionPlanUpdate, SubscriptionPlanResponse,
    TargetResourceCreate, TargetResourceUpdate, TargetResourceResponse,
    BotConfigUpdate, ManagedBotResponse, BroadcastRequest, PendingSubscriptionResponse,
    PendingSubscriptionStatusEnum
)
from app.repositories.subscription_plan import SubscriptionPlanRepository # Assumed created
from app.repositories.target_resource import TargetResourceRepository # Assumed created
from app.repositories.pending_subscription import PendingSubscriptionRepository
from app.repositories.managed_bot import ManagedBotRepository
from app.services.config_service import ConfigService # Assumed created
from app.services.broadcast_service import BroadcastService
from app.services.subscription_manager import SubscriptionManager
from app.services.access_granter import AccessGranter # Assumed created
from app.dependencies.auth import get_current_user
from app.models.models import PlatformUser
from typing import List, Dict, Any
import logging

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/admin/bots/{managed_bot_id}", tags=["Admin - Bot Management"])

# --- Subscription Plan Endpoints ---

@router.post("/subscription-plans", response_model=SubscriptionPlanResponse, status_code=201)
async def create_subscription_plan(
    managed_bot_id: int, plan: SubscriptionPlanCreate, db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_user)
):
    """Create a new subscription plan for a specific managed bot."""
    # Ensure the plan belongs to the correct bot
    if plan.managed_bot_id != managed_bot_id:
        raise HTTPException(status_code=400, detail="Managed bot ID mismatch")
    # Check if bot exists
    bot = ManagedBotRepository.get_by_id(db, managed_bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Managed bot not found")
    
    # Verify the bot belongs to the authenticated user
    if bot.platform_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You don't have permission to access this bot")
    
    # Validate linked_resource_ids belong to this bot
    if plan.linked_resource_ids:
        for resource_id in plan.linked_resource_ids:
            resource = TargetResourceRepository.get_by_id(db, resource_id)
            if not resource or resource.managed_bot_id != managed_bot_id:
                raise HTTPException(status_code=400, detail=f"Resource with ID {resource_id} does not exist or does not belong to this bot")
    
    return SubscriptionPlanRepository.create(db, plan)


@router.get("/subscription-plans", response_model=List[SubscriptionPlanResponse])
async def get_subscription_plans_for_bot(
    managed_bot_id: int, db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_user)
):
    """Get all subscription plans for a specific managed bot."""
    bot = ManagedBotRepository.get_by_id(db, managed_bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Managed bot not found")
    
    # Verify the bot belongs to the authenticated user
    if bot.platform_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You don't have permission to access this bot")
    return SubscriptionPlanRepository.get_by_managed_bot(db, managed_bot_id)


@router.get("/subscription-plans/{plan_id}", response_model=SubscriptionPlanResponse)
async def get_subscription_plan(
    managed_bot_id: int, plan_id: int, db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_user)
):
    """Get a specific subscription plan by ID."""
    plan = SubscriptionPlanRepository.get_by_id_and_bot(db, plan_id, managed_bot_id) # Requires implementation
    if not plan:
        raise HTTPException(status_code=404, detail="Subscription plan not found for this bot")
    return plan


@router.put("/subscription-plans/{plan_id}", response_model=SubscriptionPlanResponse)
async def update_subscription_plan(
    managed_bot_id: int, plan_id: int, plan_update: SubscriptionPlanUpdate, db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_user)
):
    """Update a specific subscription plan."""
    plan = SubscriptionPlanRepository.get_by_id_and_bot(db, plan_id, managed_bot_id) # Requires implementation
    if not plan:
        raise HTTPException(status_code=404, detail="Subscription plan not found for this bot")
    
    # Ensure update doesn't change managed_bot_id if provided
    if plan_update.managed_bot_id is not None and plan_update.managed_bot_id != managed_bot_id:
         raise HTTPException(status_code=400, detail="Cannot change managed bot ID")

    # Validate linked_resource_ids belong to this bot
    if plan_update.linked_resource_ids is not None:
        for resource_id in plan_update.linked_resource_ids:
            resource = TargetResourceRepository.get_by_id(db, resource_id)
            if not resource or resource.managed_bot_id != managed_bot_id:
                raise HTTPException(status_code=400, detail=f"Resource with ID {resource_id} does not exist or does not belong to this bot")

    updated_plan = SubscriptionPlanRepository.update(db, plan_id, plan_update)
    if not updated_plan: # Should not happen if get_by_id found it, but good practice
         raise HTTPException(status_code=404, detail="Subscription plan not found during update")
    return updated_plan


@router.delete("/subscription-plans/{plan_id}", status_code=204)
async def delete_subscription_plan(
    managed_bot_id: int, plan_id: int, db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_user)
):
    """Delete a specific subscription plan."""
    plan = SubscriptionPlanRepository.get_by_id_and_bot(db, plan_id, managed_bot_id) # Requires implementation
    if not plan:
        raise HTTPException(status_code=404, detail="Subscription plan not found for this bot")
    
    # Consider checks: are there active subscriptions using this plan?
    
    deleted = SubscriptionPlanRepository.delete(db, plan_id)
    if not deleted:
        raise HTTPException(status_code=500, detail="Failed to delete subscription plan")
    return None


# --- Target Resource Endpoints ---

@router.post("/target-resources", response_model=TargetResourceResponse, status_code=201)
async def create_target_resource(
    managed_bot_id: int, resource: TargetResourceCreate, db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_user)
):
    """Create a new target resource for a specific managed bot."""
    if resource.managed_bot_id != managed_bot_id:
        raise HTTPException(status_code=400, detail="Managed bot ID mismatch")
    bot = ManagedBotRepository.get_by_id(db, managed_bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Managed bot not found")
    
    # Verify the bot belongs to the authenticated user
    if bot.platform_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You don't have permission to access this bot")
    return TargetResourceRepository.create(db, resource)


@router.get("/target-resources", response_model=List[TargetResourceResponse])
async def get_target_resources_for_bot(
    managed_bot_id: int, db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_user)
):
    """Get all target resources for a specific managed bot."""
    bot = ManagedBotRepository.get_by_id(db, managed_bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Managed bot not found")
    
    # Verify the bot belongs to the authenticated user
    if bot.platform_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You don't have permission to access this bot")
    return TargetResourceRepository.get_by_managed_bot(db, managed_bot_id) # Requires implementation


@router.get("/target-resources/{resource_id}", response_model=TargetResourceResponse)
async def get_target_resource(
    managed_bot_id: int, resource_id: int, db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_user)
):
    """Get a specific target resource by ID."""
    resource = TargetResourceRepository.get_by_id_and_bot(db, resource_id, managed_bot_id) # Requires implementation
    if not resource:
        raise HTTPException(status_code=404, detail="Target resource not found for this bot")
    return resource


@router.put("/target-resources/{resource_id}", response_model=TargetResourceResponse)
async def update_target_resource(
    managed_bot_id: int, resource_id: int, resource_update: TargetResourceUpdate, db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_user)
):
    """Update a specific target resource."""
    resource = TargetResourceRepository.get_by_id_and_bot(db, resource_id, managed_bot_id) # Requires implementation
    if not resource:
        raise HTTPException(status_code=404, detail="Target resource not found for this bot")
    
    if resource_update.managed_bot_id is not None and resource_update.managed_bot_id != managed_bot_id:
         raise HTTPException(status_code=400, detail="Cannot change managed bot ID")

    updated_resource = TargetResourceRepository.update(db, resource_id, resource_update)
    if not updated_resource:
         raise HTTPException(status_code=404, detail="Target resource not found during update")
    return updated_resource


@router.delete("/target-resources/{resource_id}", status_code=204)
async def delete_target_resource(
    managed_bot_id: int, resource_id: int, db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_user)
):
    """Delete a specific target resource."""
    resource = TargetResourceRepository.get_by_id_and_bot(db, resource_id, managed_bot_id) # Requires implementation
    if not resource:
        raise HTTPException(status_code=404, detail="Target resource not found for this bot")
    
    # Consider checks: is this resource linked in any plans?
    
    deleted = TargetResourceRepository.delete(db, resource_id)
    if not deleted:
        raise HTTPException(status_code=500, detail="Failed to delete target resource")
    return None


# --- Bot Configuration Endpoint ---

@router.get("/config", response_model=Dict[str, Any])
async def get_bot_config(
    managed_bot_id: int, db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_user)
):
    """Get the configuration data for the managed bot."""
    config = ConfigService.get_config(db, managed_bot_id)
    if config is None: # Check if bot exists via config service or repo
        raise HTTPException(status_code=404, detail="Managed bot not found")
    return config


@router.put("/config", response_model=Dict[str, Any])
async def update_bot_config(
    managed_bot_id: int, config_update: BotConfigUpdate, db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_user)
):
    """Update the configuration data for the managed bot."""
    updated_config = ConfigService.update_config(db, managed_bot_id, config_update)
    if updated_config is None:
        raise HTTPException(status_code=404, detail="Managed bot not found")
    return updated_config


# --- Broadcast Endpoint ---

@router.post("/broadcast", status_code=202)
async def broadcast_message(
    managed_bot_id: int, broadcast_request: BroadcastRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_user)
):
    """Initiate a broadcast message to subscribers of the managed bot."""
    if broadcast_request.managed_bot_id != managed_bot_id:
         raise HTTPException(status_code=400, detail="Managed bot ID mismatch")

    bot = ManagedBotRepository.get_by_id(db, managed_bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Managed bot not found")
    
    # Verify the bot belongs to the authenticated user
    if bot.platform_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You don't have permission to access this bot")

    logger.info(f"Adding broadcast task for bot {managed_bot_id}")
    background_tasks.add_task(
        BroadcastService.broadcast_task,
        managed_bot_id=managed_bot_id,
        message_text=broadcast_request.message_text,
        target_user_ids=broadcast_request.target_user_ids
    )
    return {"message": "Broadcast task accepted"}


# --- Pending Subscription Management ---

@router.get("/pending-subscriptions", response_model=List[PendingSubscriptionResponse])
async def list_pending_subscriptions(
    managed_bot_id: int, db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_user)
):
    """List pending subscription requests for the managed bot."""
    bot = ManagedBotRepository.get_by_id(db, managed_bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Managed bot not found")
    
    # Verify the bot belongs to the authenticated user
    if bot.platform_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You don't have permission to access this bot")
    return await SubscriptionManager.get_pending_subscriptions_by_managed_bot(db, managed_bot_id)


@router.post("/pending-subscriptions/{pending_sub_id}/approve", response_model=Dict[str, Any])
async def approve_pending_subscription(
    managed_bot_id: int, pending_sub_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_user)
):
    """Approve a pending subscription request."""
    # Get the managed bot and verify ownership
    bot = ManagedBotRepository.get_by_id(db, managed_bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Managed bot not found")
    
    # Verify the bot belongs to the authenticated user
    if bot.platform_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You don't have permission to access this bot")
        
    # Get the managed bot and verify ownership
    bot = ManagedBotRepository.get_by_id(db, managed_bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Managed bot not found")
    
    # Verify the bot belongs to the authenticated user
    if bot.platform_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You don't have permission to access this bot")
        
    pending_sub = PendingSubscriptionRepository.get_by_id(db, pending_sub_id)
    if not pending_sub or pending_sub.managed_bot_id != managed_bot_id:
        raise HTTPException(status_code=404, detail="Pending subscription not found for this bot")
    if pending_sub.status != PendingSubscriptionStatusEnum.pending_approval:
        raise HTTPException(status_code=400, detail=f"Subscription already processed: {pending_sub.status.value}")

    # Approve subscription (creates active sub)
    result = await SubscriptionManager.approve_pending_subscription(db, pending_sub_id)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("message", "Failed to approve subscription"))

    # Grant access in the background
    new_subscription = result.get("subscription")
    if new_subscription:
         logger.info(f"Adding access grant task for subscription {new_subscription.id}")
         background_tasks.add_task(
             AccessGranter.grant_access_task,
             subscription_id=new_subscription.id
         )
         # Optionally: Notify user via TG in background task

    return {"message": "Subscription approved, access granting initiated.", "subscription_id": new_subscription.id if new_subscription else None}


@router.post("/pending-subscriptions/{pending_sub_id}/reject", response_model=Dict[str, Any])
async def reject_pending_subscription(
    managed_bot_id: int, pending_sub_id: int, db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_user)
):
    """Reject a pending subscription request."""
    # Get the managed bot and verify ownership
    bot = ManagedBotRepository.get_by_id(db, managed_bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Managed bot not found")
    
    # Verify the bot belongs to the authenticated user
    if bot.platform_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You don't have permission to access this bot")
        
    # Get the managed bot and verify ownership
    bot = ManagedBotRepository.get_by_id(db, managed_bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Managed bot not found")
    
    # Verify the bot belongs to the authenticated user
    if bot.platform_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You don't have permission to access this bot")
        
    pending_sub = PendingSubscriptionRepository.get_by_id(db, pending_sub_id)
    if not pending_sub or pending_sub.managed_bot_id != managed_bot_id:
        raise HTTPException(status_code=404, detail="Pending subscription not found for this bot")
    if pending_sub.status != PendingSubscriptionStatusEnum.pending_approval:
        raise HTTPException(status_code=400, detail=f"Subscription already processed: {pending_sub.status.value}")

    result = await SubscriptionManager.reject_pending_subscription(db, pending_sub_id)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("message", "Failed to reject subscription"))
    
    # Optionally: Notify user via TG that request was rejected

    return {"message": "Subscription request rejected."}