from fastapi import BackgroundTasks
from sqlalchemy.orm import Session
from app.services.telegram_api import TelegramAPIWrapper
from app.repositories.managed_bot import ManagedBotRepository
from app.repositories.subscription_plan import SubscriptionPlanRepository
from app.repositories.target_resource import TargetResourceRepository
from app.repositories.pending_subscription import PendingSubscriptionRepository
from app.utils.telegram_ui import (
    create_main_admin_menu,
    create_resource_management_menu,
    create_pending_subscription_menu,
    create_pending_subscription_action_menu,
    create_settings_menu,
    create_broadcast_menu,
    create_back_button
)
from typing import Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


async def handle_admin_menu(user_id: int, action: str, managed_bot, telegram_api: TelegramAPIWrapper, db: Session):
    """Handle admin menu navigation and actions"""
    # Verify user is the platform user who owns the bot
    if managed_bot.platform_user_id != user_id:
        await telegram_api.send_message(
            chat_id=user_id,
            text="You don't have permission to access the admin menu."
        )
        return {"status": "error", "message": "Unauthorized"}
    
    if action == "main":
        # Show main admin menu
        reply_markup = create_main_admin_menu()
        await telegram_api.send_message(
            chat_id=user_id,
            text="Admin Menu - Select an option:",
            reply_markup=reply_markup
        )
    
    elif action == "manage_plans":
        # Show subscription plans management
        plans = SubscriptionPlanRepository.get_by_managed_bot(db, managed_bot.id)
        
        if not plans:
            # No plans exist yet
            await telegram_api.send_message(
                chat_id=user_id,
                text="You don't have any subscription plans yet. Would you like to create one?",
                reply_markup=create_back_button("admin:main")
            )
        else:
            # List existing plans
            plan_list = "\n".join([f"- {plan.name} ({plan.duration_days} days)" for plan in plans])
            await telegram_api.send_message(
                chat_id=user_id,
                text=f"Your subscription plans:\n{plan_list}\n\nUse /create_plan to add a new plan.",
                reply_markup=create_back_button("admin:main")
            )
    
    elif action == "manage_resources":
        # Show resources management
        resources = TargetResourceRepository.get_by_managed_bot(db, managed_bot.id)
        reply_markup = create_resource_management_menu(resources)
        
        await telegram_api.send_message(
            chat_id=user_id,
            text="Resource Management - Select a resource to manage:",
            reply_markup=reply_markup
        )
    
    elif action == "pending_subs":
        # Show pending subscriptions
        pending_subs = PendingSubscriptionRepository.get_pending_by_managed_bot(db, managed_bot.id)
        
        if not pending_subs:
            await telegram_api.send_message(
                chat_id=user_id,
                text="There are no pending subscription requests at the moment.",
                reply_markup=create_back_button("admin:main")
            )
        else:
            reply_markup = create_pending_subscription_menu(pending_subs)
            await telegram_api.send_message(
                chat_id=user_id,
                text=f"You have {len(pending_subs)} pending subscription requests. Select one to view details:",
                reply_markup=reply_markup
            )
    
    elif action == "broadcast":
        # Show broadcast options
        reply_markup = create_broadcast_menu()
        await telegram_api.send_message(
            chat_id=user_id,
            text="Broadcast Message - Select an option:",
            reply_markup=reply_markup
        )
    
    elif action == "settings":
        # Show bot settings
        config = managed_bot.config_data or {}
        reply_markup = create_settings_menu(config)
        
        await telegram_api.send_message(
            chat_id=user_id,
            text="Bot Settings - Select an option to configure:",
            reply_markup=reply_markup
        )
    
    return {"status": "ok"}


async def handle_settings_menu(user_id: int, setting_type: str, managed_bot, telegram_api: TelegramAPIWrapper, db: Session):
    """Handle settings menu options"""
    # Verify user is the platform user who owns the bot
    if managed_bot.platform_user_id != user_id:
        await telegram_api.send_message(
            chat_id=user_id,
            text="You don't have permission to access the settings menu."
        )
        return {"status": "error", "message": "Unauthorized"}
    
    config = managed_bot.config_data or {}
    
    if setting_type == "welcome":
        # Edit welcome message
        current_message = config.get("welcome_message", "Welcome to our subscription bot!")
        await telegram_api.send_message(
            chat_id=user_id,
            text=f"Current welcome message:\n\n\"{current_message}\"\n\nTo change it, send a new message starting with /set_welcome followed by your new welcome message.",
            reply_markup=create_back_button("admin:settings")
        )
    
    elif setting_type == "subscription":
        # Edit subscription messages
        subscription_message = config.get("subscription_message", "Thank you for subscribing!")
        expired_message = config.get("expired_message", "Your subscription has expired.")
        
        await telegram_api.send_message(
            chat_id=user_id,
            text=f"Current subscription messages:\n\n1. Subscription message:\n\"{subscription_message}\"\n\n2. Expired message:\n\"{expired_message}\"\n\nTo change them, use:\n/set_subscription_msg [new message]\n/set_expired_msg [new message]",
            reply_markup=create_back_button("admin:settings")
        )
    
    elif setting_type == "approval":
        # Edit approval messages
        pending_message = config.get("pending_message", "Your subscription request is pending approval.")
        approved_message = config.get("approved_message", "Your subscription request has been approved!")
        rejected_message = config.get("rejected_message", "Your subscription request has been rejected.")
        
        await telegram_api.send_message(
            chat_id=user_id,
            text=f"Current approval messages:\n\n1. Pending message:\n\"{pending_message}\"\n\n2. Approved message:\n\"{approved_message}\"\n\n3. Rejected message:\n\"{rejected_message}\"\n\nTo change them, use:\n/set_pending_msg [new message]\n/set_approved_msg [new message]\n/set_rejected_msg [new message]",
            reply_markup=create_back_button("admin:settings")
        )
    
    elif setting_type == "payment":
        # Payment settings
        payment_methods = config.get("intended_payment_methods", [])
        
        # Use the new payment methods menu with inline buttons
        await telegram_api.send_message(
            chat_id=user_id,
            text=f"Payment Method Settings\n\nConfigure the payment methods you accept for subscriptions. These will be shown to users when they subscribe.\n\nCurrent payment methods: {len(payment_methods)}",
            reply_markup=create_payment_methods_menu(payment_methods)
        )
    
    return {"status": "ok"}


async def handle_resource_action(user_id: int, resource_param: str, managed_bot, telegram_api: TelegramAPIWrapper, db: Session):
    """Handle resource management actions"""
    # Verify user is the platform user who owns the bot
    if managed_bot.platform_user_id != user_id:
        await telegram_api.send_message(
            chat_id=user_id,
            text="You don't have permission to manage resources."
        )
        return {"status": "error", "message": "Unauthorized"}
    
    if resource_param == "add":
        # Show instructions for adding a new resource
        await telegram_api.send_message(
            chat_id=user_id,
            text="To add a new resource, use one of the following commands:\n\n/add_channel [chat_id] [invite_link_type]\n/add_group [chat_id] [invite_link_type]\n\nInvite link types: unique, static, request, custom",
            reply_markup=create_back_button("admin:manage_resources")
        )
    else:
        try:
            # View specific resource details
            resource_id = int(resource_param)
            resource = TargetResourceRepository.get_by_id(db, resource_id)
            
            if not resource or resource.managed_bot_id != managed_bot.id:
                await telegram_api.send_message(
                    chat_id=user_id,
                    text="Resource not found.",
                    reply_markup=create_back_button("admin:manage_resources")
                )
                return {"status": "error", "message": "Resource not found"}
            
            # Show resource details
            resource_type = "Channel" if resource.type.value == "channel" else "Group"
            invite_type = resource.invite_link_type.value.capitalize()
            
            await telegram_api.send_message(
                chat_id=user_id,
                text=f"Resource Details:\n\nType: {resource_type}\nChat ID: {resource.tg_chat_id}\nInvite Link Type: {invite_type}\nMandatory: {'Yes' if resource.is_mandatory else 'No'}\n\nTo delete this resource, use:\n/delete_resource {resource.id}",
                reply_markup=create_back_button("admin:manage_resources")
            )
        except ValueError:
            await telegram_api.send_message(
                chat_id=user_id,
                text="Invalid resource ID.",
                reply_markup=create_back_button("admin:manage_resources")
            )
    
    return {"status": "ok"}


async def handle_view_pending_subscription(user_id: int, pending_sub_id: int, managed_bot, telegram_api: TelegramAPIWrapper, db: Session):
    """Handle viewing details of a pending subscription"""
    # Verify user is the platform user who owns the bot
    if managed_bot.platform_user_id != user_id:
        await telegram_api.send_message(
            chat_id=user_id,
            text="You don't have permission to view pending subscriptions."
        )
        return {"status": "error", "message": "Unauthorized"}
    
    # Get pending subscription details
    pending_sub = PendingSubscriptionRepository.get_by_id(db, pending_sub_id)
    
    if not pending_sub or pending_sub.managed_bot_id != managed_bot.id:
        await telegram_api.send_message(
            chat_id=user_id,
            text="Pending subscription not found.",
            reply_markup=create_back_button("admin:pending_subs")
        )
        return {"status": "error", "message": "Pending subscription not found"}
    
    # Get related data
    plan = SubscriptionPlanRepository.get_by_id(db, pending_sub.plan_id)
    
    # Create approval/rejection buttons
    reply_markup = create_pending_subscription_action_menu(pending_sub.id)
    
    # Format and send details
    await telegram_api.send_message(
        chat_id=user_id,
        text=f"Pending Subscription Details:\n\nUser ID: {pending_sub.end_user_id}\nPlan: {plan.name} ({plan.duration_days} days)\nStatus: {pending_sub.status.value}\nRequested: {pending_sub.created_at}\n\nPlease approve or reject this subscription request:",
        reply_markup=reply_markup
    )
    
    return {"status": "ok"}