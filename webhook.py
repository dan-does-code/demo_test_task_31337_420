from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Path, Request
from sqlalchemy.orm import Session
from app.models.base import get_db
from app.schemas.schemas import TelegramUpdate, EndUserCreate
from app.repositories.managed_bot import ManagedBotRepository
from app.repositories.end_user import EndUserRepository
from app.repositories.subscription_plan import SubscriptionPlanRepository
from app.repositories.pending_subscription import PendingSubscriptionRepository
from app.repositories.target_resource import TargetResourceRepository
from app.services.telegram_api import TelegramAPIWrapper
from app.services.subscription_manager import SubscriptionManager
from app.services.access_granter import AccessGranter
from app.utils.telegram_ui import (
    create_main_admin_menu,
    create_plan_selection_menu,
    create_resource_management_menu,
    create_pending_subscription_menu,
    create_pending_subscription_action_menu,
    create_settings_menu,
    create_broadcast_menu,
    create_confirmation_menu,
    create_back_button
)
from app.routers.admin_handlers import (
    handle_admin_menu,
    handle_settings_menu,
    handle_resource_action,
    handle_view_pending_subscription
)
from app.services.config_service import ConfigService
from app.schemas.schemas import TargetResourceCreate, SubscriptionPlanCreate
from app.models.models import ResourceType, InviteLinkType
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import Dict, Any, List, Optional
from app.utils.logger import get_logger

# Get logger for this module
logger = get_logger(__name__)

# Create router
router = APIRouter(prefix="/webhook", tags=["Telegram Webhook"])


@router.post("/{webhook_secret}")
async def handle_telegram_update(
    webhook_secret: str = Path(..., description="Unique webhook secret for bot identification"),
    update: TelegramUpdate = None,
    request: Request = None,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """Handle incoming Telegram updates"""
    # If update is None, try to parse from request body
    if update is None:
        try:
            update_data = await request.json()
            update = TelegramUpdate.parse_obj(update_data)
        except Exception as e:
            logger.error(f"Error parsing update: {e}")
            raise HTTPException(status_code=400, detail="Invalid update format")
    
    # Find the managed bot by webhook secret
    target_bot = ManagedBotRepository.get_by_webhook_secret(db, webhook_secret)
    
    if not target_bot:
        logger.error(f"Bot not found for webhook secret")
        raise HTTPException(status_code=404, detail="Bot not found")
    
    # Initialize Telegram API wrapper
    bot_token = ManagedBotRepository.get_decrypted_token(db, target_bot.id)
    telegram_api = TelegramAPIWrapper(bot_token)
    
    # Process the update based on its type
    if update.message:
        return await process_message(update, target_bot, telegram_api, db, background_tasks)
    elif update.callback_query:
        return await process_callback_query(update, target_bot, telegram_api, db, background_tasks)
    
    return {"status": "ok"}


async def process_message(update: TelegramUpdate, managed_bot, telegram_api: TelegramAPIWrapper, db: Session, background_tasks: BackgroundTasks):
    """Process incoming message updates"""
    message = update.message
    user = message.from_user
    chat_id = message.chat.id
    
    if not user:
        return {"status": "ok"}  # Ignore messages without user info
    
    # Check if user exists, create if not
    end_user = EndUserRepository.get_by_tg_user_id(db, user.id)
    if not end_user:
        user_data = EndUserCreate(
            tg_user_id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            username=user.username
        )
        end_user = EndUserRepository.create(db, user_data)
    
    # Process commands
    if message.text and message.text.startswith('/'):
        command_parts = message.text.split(' ')
        command = command_parts[0].lower()
        args = command_parts[1:] if len(command_parts) > 1 else []
        
        # Check if user is the bot owner for admin commands
        is_admin = managed_bot.platform_user_id == user.id
        
        if command == '/start':
            return await handle_start_command(user.id, managed_bot, telegram_api, db)
        
        elif command == '/subscribe':
            return await handle_subscribe_command(user.id, managed_bot, telegram_api, db)
        
        # Admin commands - only process if user is the bot owner
        elif is_admin:
            # Settings commands
            if command == '/set_welcome' and args:
                return await handle_set_welcome(user.id, ' '.join(args), managed_bot, telegram_api, db)
            
            elif command == '/set_subscription_msg' and args:
                return await handle_set_config(user.id, 'subscription_message', ' '.join(args), managed_bot, telegram_api, db)
            
            elif command == '/set_expired_msg' and args:
                return await handle_set_config(user.id, 'expired_message', ' '.join(args), managed_bot, telegram_api, db)
            
            elif command == '/set_pending_msg' and args:
                return await handle_set_config(user.id, 'pending_message', ' '.join(args), managed_bot, telegram_api, db)
            
            elif command == '/set_approved_msg' and args:
                return await handle_set_config(user.id, 'approved_message', ' '.join(args), managed_bot, telegram_api, db)
            
            elif command == '/set_rejected_msg' and args:
                return await handle_set_config(user.id, 'rejected_message', ' '.join(args), managed_bot, telegram_api, db)
            
            # Payment method commands
            elif command == '/add_payment_method' and args:
                return await handle_payment_method(user.id, 'add', args[0], managed_bot, telegram_api, db)
            
            elif command == '/remove_payment_method' and args:
                return await handle_payment_method(user.id, 'remove', args[0], managed_bot, telegram_api, db)
            
            # Resource management commands
            elif command == '/add_channel' and len(args) >= 2:
                return await handle_add_resource(user.id, 'channel', args[0], args[1], managed_bot, telegram_api, db)
            
            elif command == '/add_group' and len(args) >= 2:
                return await handle_add_resource(user.id, 'group', args[0], args[1], managed_bot, telegram_api, db)
            
            elif command == '/delete_resource' and args:
                return await handle_delete_resource(user.id, args[0], managed_bot, telegram_api, db)
            
            # Plan management commands
            elif command == '/create_plan':
                return await handle_create_plan_command(user.id, managed_bot, telegram_api, db)
        
        # If we get here, the command wasn't recognized
        await telegram_api.send_message(
            chat_id=chat_id,
            text="I'm sorry, I don't understand that command. Try /start or /subscribe."
        )
        return {"status": "ok"}
    
    # Default response for non-command messages
    await telegram_api.send_message(
        chat_id=chat_id,
        text="I'm sorry, I don't understand that message. Try /start or /subscribe."
    )
    
    return {"status": "ok"}


async def process_callback_query(update: TelegramUpdate, managed_bot, telegram_api: TelegramAPIWrapper, db: Session, background_tasks: BackgroundTasks):
    """Process callback query updates (inline button clicks)"""
    callback_query = update.callback_query
    user_id = callback_query.from_user.id
    callback_data = callback_query.data
    
    if not callback_data:
        return {"status": "ok"}
    
    # Parse callback data (format: action:param1:param2...)
    parts = callback_data.split(':')
    action = parts[0]
    
    # Handle payment method actions
    if action == "add_payment_method":
        # Show prompt to add a new payment method
        await telegram_api.send_message(
            chat_id=user_id,
            text="Please send a message with the command:\n/add_payment_method [method name]\n\nFor example:\n/add_payment_method Bank Transfer",
            reply_markup=create_back_button("settings:payment")
        )
        await telegram_api.answer_callback_query(callback_query.id)
        return {"status": "ok"}
        
    elif action == "remove_payment_method" and len(parts) > 1:
        # Remove the payment method directly
        method = parts[1]
        return await handle_payment_method(user_id, 'remove', method, managed_bot, telegram_api, db)
        
    elif action == "payment_method_info" and len(parts) > 1:
        # Show information about the payment method
        method = parts[1]
        await telegram_api.send_message(
            chat_id=user_id,
            text=f"Payment Method: {method}\n\nThis payment method is currently active and will be shown to users when they subscribe.\n\nTo remove this payment method, click the Remove button.",
            reply_markup=create_back_button("settings:payment")
        )
        await telegram_api.answer_callback_query(callback_query.id)
        return {"status": "ok"}
    
    # Handle subscription plan selection
    if action == "select_plan":
        if len(parts) > 1:
            plan_id = int(parts[1])
            return await handle_plan_selection(user_id, plan_id, managed_bot.id, telegram_api, db)
    
    # Handle admin approval/rejection of pending subscriptions
    elif action == "admin_approve":
        if len(parts) > 1:
            pending_sub_id = int(parts[1])
            return await handle_admin_approval(user_id, pending_sub_id, managed_bot.id, telegram_api, db, background_tasks)
    
    elif action == "admin_reject":
        if len(parts) > 1:
            pending_sub_id = int(parts[1])
            return await handle_admin_rejection(user_id, pending_sub_id, managed_bot.id, telegram_api, db)
    
    # Handle admin menu navigation
    elif action == "admin":
        if len(parts) > 1:
            return await handle_admin_menu(user_id, parts[1], managed_bot, telegram_api, db)
    
    # Handle settings menu navigation
    elif action == "settings":
        if len(parts) > 1:
            return await handle_settings_menu(user_id, parts[1], managed_bot, telegram_api, db)
    
    # Handle resource management
    elif action == "resource":
        if len(parts) > 1:
            return await handle_resource_action(user_id, parts[1], managed_bot, telegram_api, db)
    
    # Handle viewing pending subscription details
    elif action == "view_pending":
        if len(parts) > 1:
            pending_sub_id = int(parts[1])
            return await handle_view_pending_subscription(user_id, pending_sub_id, managed_bot, telegram_api, db)
    
    # Handle cancel action
    elif action == "cancel":
        await telegram_api.send_message(
            chat_id=user_id,
            text="Action cancelled."
        )
        return {"status": "ok"}
    
    # Default response for unknown callback data
    await telegram_api.send_message(
        chat_id=user_id,
        text="I'm sorry, I couldn't process your request."
    )
    
    return {"status": "ok"}


async def handle_start_command(user_id: int, managed_bot, telegram_api: TelegramAPIWrapper, db: Session):
    """Handle /start command"""
    # Get bot configuration
    config = managed_bot.config_data or {}
    welcome_message = config.get("welcome_message", "Welcome to our subscription bot!")
    
    # Create inline keyboard with subscription button
    keyboard = [
        [InlineKeyboardButton("Subscribe", callback_data="select_plan")]
    ]
    
    # Add admin button if user is the platform user who owns the bot
    if managed_bot.platform_user_id == user_id:
        keyboard.append([InlineKeyboardButton("Admin Menu", callback_data="admin:main")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send welcome message
    await telegram_api.send_message(
        chat_id=user_id,
        text=welcome_message,
        reply_markup=reply_markup
    )
    
    return {"status": "ok"}


async def handle_subscribe_command(user_id: int, managed_bot, telegram_api: TelegramAPIWrapper, db: Session):
    """Handle /subscribe command"""
    # Get available subscription plans
    plans = SubscriptionPlanRepository.get_by_managed_bot(db, managed_bot.id)
    visible_plans = [plan for plan in plans if plan.is_visible]
    
    if not visible_plans:
        await telegram_api.send_message(
            chat_id=user_id,
            text="There are no subscription plans available at the moment.",
            reply_markup=create_back_button("cancel")
        )
        return {"status": "ok"}
    
    # Create plan selection menu using the UI generator
    reply_markup = create_plan_selection_menu(visible_plans)
    
    # Send plan selection message
    await telegram_api.send_message(
        chat_id=user_id,
        text="Please select a subscription plan:",
        reply_markup=reply_markup
    )
    
    return {"status": "ok"}


async def handle_plan_selection(user_id: int, plan_id: int, managed_bot_id: int, telegram_api: TelegramAPIWrapper, db: Session):
    """Handle plan selection from inline keyboard"""
    # Create pending subscription
    result = await SubscriptionManager.create_pending_subscription(db, user_id, managed_bot_id, plan_id)
    
    if not result["success"]:
        await telegram_api.send_message(
            chat_id=user_id,
            text=f"Error: {result['message']}"
        )
        return {"status": "error", "message": result["message"]}
    
    # Get bot configuration
    managed_bot = ManagedBotRepository.get_by_id(db, managed_bot_id)
    config = managed_bot.config_data or {}
    pending_message = config.get(
        "pending_message", 
        "Your subscription request has been submitted and is pending approval. You will be notified once it's processed."
    )
    
    # Send confirmation message
    await telegram_api.send_message(
        chat_id=user_id,
        text=pending_message
    )
    
    # Notify admin about new pending subscription
    # This would typically send a message to the platform user who owns the bot
    # with approval buttons
    
    return {"status": "ok"}


async def handle_admin_approval(admin_id: int, pending_sub_id: int, managed_bot_id: int, telegram_api: TelegramAPIWrapper, db: Session, background_tasks: BackgroundTasks):
    """Handle admin approval of pending subscription"""
    # Verify admin is the platform user who owns the bot
    managed_bot = ManagedBotRepository.get_by_id(db, managed_bot_id)
    if not managed_bot or managed_bot.platform_user_id != admin_id:
        await telegram_api.send_message(
            chat_id=admin_id,
            text="You don't have permission to approve this subscription.",
            reply_markup=create_back_button("admin:main")
        )
        return {"status": "error", "message": "Unauthorized"}
    
    # Approve the subscription
    result = await SubscriptionManager.approve_pending_subscription(db, pending_sub_id)
    
    if not result["success"]:
        await telegram_api.send_message(
            chat_id=admin_id,
            text=f"Error: {result['message']}",
            reply_markup=create_back_button("admin:pending_subs")
        )
        return {"status": "error", "message": result["message"]}
    
    # Get the end user ID from the pending subscription
    pending_sub = PendingSubscriptionRepository.get_by_id(db, pending_sub_id)
    end_user_id = pending_sub.end_user_id
    
    # Get bot configuration
    config = managed_bot.config_data or {}
    approved_message = config.get(
        "approved_message", 
        "Your subscription request has been approved! You now have access to the subscribed resources."
    )
    
    # Notify the end user
    await telegram_api.send_message(
        chat_id=end_user_id,
        text=approved_message
    )
    
    # Notify the admin
    await telegram_api.send_message(
        chat_id=admin_id,
        text=f"Subscription for user {end_user_id} has been approved.",
        reply_markup=create_back_button("admin:pending_subs")
    )
    
    # Grant access in the background
    new_subscription = result.get("subscription")
    if new_subscription:
        background_tasks.add_task(
            AccessGranter.grant_access_task,
            subscription_id=new_subscription.id
        )
    
    return {"status": "ok"}


async def handle_admin_rejection(admin_id: int, pending_sub_id: int, managed_bot_id: int, telegram_api: TelegramAPIWrapper, db: Session):
    """Handle admin rejection of pending subscription"""
    # Verify admin is the platform user who owns the bot
    managed_bot = ManagedBotRepository.get_by_id(db, managed_bot_id)
    if not managed_bot or managed_bot.platform_user_id != admin_id:
        await telegram_api.send_message(
            chat_id=admin_id,
            text="You don't have permission to reject this subscription.",
            reply_markup=create_back_button("admin:main")
        )
        return {"status": "error", "message": "Unauthorized"}
    
    # Reject the subscription
    result = await SubscriptionManager.reject_pending_subscription(db, pending_sub_id)
    
    if not result["success"]:
        await telegram_api.send_message(
            chat_id=admin_id,
            text=f"Error: {result['message']}",
            reply_markup=create_back_button("admin:pending_subs")
        )
        return {"status": "error", "message": result["message"]}
    
    # Get the end user ID from the pending subscription
    pending_sub = PendingSubscriptionRepository.get_by_id(db, pending_sub_id)
    end_user_id = pending_sub.end_user_id
    
    # Get bot configuration
    config = managed_bot.config_data or {}
    rejected_message = config.get(
        "rejected_message", 
        "Your subscription request has been rejected. Please contact the administrator for more information."
    )
    
    # Notify the end user
    await telegram_api.send_message(
        chat_id=end_user_id,
        text=rejected_message
    )
    
    # Notify the admin
    await telegram_api.send_message(
        chat_id=admin_id,
        text=f"Subscription for user {end_user_id} has been rejected.",
        reply_markup=create_back_button("admin:pending_subs")
    )
    
    return {"status": "ok"}


async def handle_set_welcome(user_id: int, message: str, managed_bot, telegram_api: TelegramAPIWrapper, db: Session):
    """Handle setting welcome message"""
    # Verify user is the platform user who owns the bot
    if managed_bot.platform_user_id != user_id:
        await telegram_api.send_message(
            chat_id=user_id,
            text="You don't have permission to change bot settings."
        )
        return {"status": "error", "message": "Unauthorized"}
    
    # Update the welcome message in the bot's config
    config = managed_bot.config_data or {}
    config["welcome_message"] = message
    
    # Save the updated config
    ConfigService.update_config_field(db, managed_bot.id, "welcome_message", message)
    
    # Confirm to the admin
    await telegram_api.send_message(
        chat_id=user_id,
        text=f"Welcome message updated successfully. New message:\n\n\"{message}\"",
        reply_markup=create_back_button("admin:settings")
    )
    
    return {"status": "ok"}


async def handle_set_config(user_id: int, config_key: str, value: str, managed_bot, telegram_api: TelegramAPIWrapper, db: Session):
    """Handle setting various config values"""
    # Verify user is the platform user who owns the bot
    if managed_bot.platform_user_id != user_id:
        await telegram_api.send_message(
            chat_id=user_id,
            text="You don't have permission to change bot settings."
        )
        return {"status": "error", "message": "Unauthorized"}
    
    # Update the config value
    config = managed_bot.config_data or {}
    config[config_key] = value
    
    # Save the updated config
    ConfigService.update_config_field(db, managed_bot.id, config_key, value)
    
    # Get a human-readable name for the config key
    config_name = {
        "subscription_message": "subscription confirmation message",
        "expired_message": "subscription expiry message",
        "pending_message": "pending subscription message",
        "approved_message": "subscription approval message",
        "rejected_message": "subscription rejection message"
    }.get(config_key, config_key)
    
    # Confirm to the admin
    await telegram_api.send_message(
        chat_id=user_id,
        text=f"The {config_name} has been updated successfully. New message:\n\n\"{value}\"",
        reply_markup=create_back_button("admin:settings")
    )
    
    return {"status": "ok"}


async def handle_payment_method(user_id: int, action: str, method: str, managed_bot, telegram_api: TelegramAPIWrapper, db: Session):
    """Handle adding or removing payment methods"""
    # Verify user is the platform user who owns the bot
    if managed_bot.platform_user_id != user_id:
        await telegram_api.send_message(
            chat_id=user_id,
            text="You don't have permission to change bot settings."
        )
        return {"status": "error", "message": "Unauthorized"}
    
    # Get current payment methods
    config = managed_bot.config_data or {}
    payment_methods = config.get("intended_payment_methods", [])
    
    if action == "add":
        # Add the method if it doesn't already exist
        if method not in payment_methods:
            payment_methods.append(method)
            message = f"Payment method '{method}' has been added."
        else:
            message = f"Payment method '{method}' already exists."
    
    elif action == "remove":
        # Remove the method if it exists
        if method in payment_methods:
            payment_methods.remove(method)
            message = f"Payment method '{method}' has been removed."
        else:
            message = f"Payment method '{method}' does not exist."
    
    # Update the config
    config["intended_payment_methods"] = payment_methods
    ConfigService.update_config_field(db, managed_bot.id, "intended_payment_methods", payment_methods)
    
    # Format the current payment methods for display
    methods_str = "\n".join([f"- {m}" for m in payment_methods]) if payment_methods else "None configured"
    
    # Confirm to the admin
    await telegram_api.send_message(
        chat_id=user_id,
        text=f"{message}\n\nCurrent payment methods:\n{methods_str}",
        reply_markup=create_back_button("admin:settings")
    )
    
    return {"status": "ok"}


async def handle_add_resource(user_id: int, resource_type: str, chat_id: str, invite_link_type: str, managed_bot, telegram_api: TelegramAPIWrapper, db: Session):
    """Handle adding a new channel or group resource"""
    # Verify user is the platform user who owns the bot
    if managed_bot.platform_user_id != user_id:
        await telegram_api.send_message(
            chat_id=user_id,
            text="You don't have permission to manage resources."
        )
        return {"status": "error", "message": "Unauthorized"}
    
    # Validate invite link type
    valid_link_types = ["unique", "static", "request", "custom"]
    if invite_link_type.lower() not in valid_link_types:
        await telegram_api.send_message(
            chat_id=user_id,
            text=f"Invalid invite link type. Valid types are: {', '.join(valid_link_types)}",
            reply_markup=create_back_button("admin:manage_resources")
        )
        return {"status": "error", "message": "Invalid invite link type"}
    
    # Map string values to enum values
    resource_type_enum = ResourceType.channel if resource_type.lower() == "channel" else ResourceType.group
    invite_link_type_enum = {
        "unique": InviteLinkType.unique,
        "static": InviteLinkType.static,
        "request": InviteLinkType.request,
        "custom": InviteLinkType.custom
    }[invite_link_type.lower()]
    
    # Create the resource
    try:
        resource_data = TargetResourceCreate(
            managed_bot_id=managed_bot.id,
            tg_chat_id=chat_id,
            type=resource_type_enum,
            invite_link_type=invite_link_type_enum,
            is_mandatory=False,  # Default value, can be changed later
            custom_link=None  # Default value, can be set later if needed
        )
        
        new_resource = TargetResourceRepository.create(db, resource_data)
        
        # Confirm to the admin
        resource_type_str = "Channel" if resource_type.lower() == "channel" else "Group"
        await telegram_api.send_message(
            chat_id=user_id,
            text=f"{resource_type_str} resource added successfully with ID: {new_resource.id}\n\nChat ID: {chat_id}\nInvite Link Type: {invite_link_type}",
            reply_markup=create_back_button("admin:manage_resources")
        )
        
        return {"status": "ok"}
    except Exception as e:
        # Handle any errors
        await telegram_api.send_message(
            chat_id=user_id,
            text=f"Error adding resource: {str(e)}",
            reply_markup=create_back_button("admin:manage_resources")
        )
        return {"status": "error", "message": str(e)}


async def handle_delete_resource(user_id: int, resource_id_str: str, managed_bot, telegram_api: TelegramAPIWrapper, db: Session):
    """Handle deleting a resource"""
    # Verify user is the platform user who owns the bot
    if managed_bot.platform_user_id != user_id:
        await telegram_api.send_message(
            chat_id=user_id,
            text="You don't have permission to manage resources."
        )
        return {"status": "error", "message": "Unauthorized"}
    
    try:
        # Convert resource_id to integer
        resource_id = int(resource_id_str)
        
        # Check if resource exists and belongs to this bot
        resource = TargetResourceRepository.get_by_id(db, resource_id)
        if not resource or resource.managed_bot_id != managed_bot.id:
            await telegram_api.send_message(
                chat_id=user_id,
                text="Resource not found or does not belong to your bot.",
                reply_markup=create_back_button("admin:manage_resources")
            )
            return {"status": "error", "message": "Resource not found"}
        
        # Check if resource is linked to any subscription plans
        plans = SubscriptionPlanRepository.get_by_managed_bot(db, managed_bot.id)
        linked_plans = []
        for plan in plans:
            if plan.linked_resource_ids and resource_id in plan.linked_resource_ids:
                linked_plans.append(plan.name)
        
        if linked_plans:
            # Resource is linked to plans, warn the admin
            plans_str = ", ".join(linked_plans)
            await telegram_api.send_message(
                chat_id=user_id,
                text=f"This resource is linked to the following subscription plans: {plans_str}\n\nPlease remove it from these plans before deleting.",
                reply_markup=create_back_button("admin:manage_resources")
            )
            return {"status": "error", "message": "Resource is linked to plans"}
        
        # Delete the resource
        deleted = TargetResourceRepository.delete(db, resource_id)
        if deleted:
            await telegram_api.send_message(
                chat_id=user_id,
                text=f"Resource with ID {resource_id} has been deleted successfully.",
                reply_markup=create_back_button("admin:manage_resources")
            )
            return {"status": "ok"}
        else:
            await telegram_api.send_message(
                chat_id=user_id,
                text=f"Failed to delete resource with ID {resource_id}.",
                reply_markup=create_back_button("admin:manage_resources")
            )
            return {"status": "error", "message": "Failed to delete resource"}
    
    except ValueError:
        # Handle invalid resource ID
        await telegram_api.send_message(
            chat_id=user_id,
            text="Invalid resource ID. Please provide a valid number.",
            reply_markup=create_back_button("admin:manage_resources")
        )
        return {"status": "error", "message": "Invalid resource ID"}


async def handle_create_plan_command(user_id: int, managed_bot, telegram_api: TelegramAPIWrapper, db: Session):
    """Handle the command to create a new subscription plan"""
    # Verify user is the platform user who owns the bot
    if managed_bot.platform_user_id != user_id:
        await telegram_api.send_message(
            chat_id=user_id,
            text="You don't have permission to manage subscription plans."
        )
        return {"status": "error", "message": "Unauthorized"}
    
    # Get available resources for this bot
    resources = TargetResourceRepository.get_by_managed_bot(db, managed_bot.id)
    if not resources:
        await telegram_api.send_message(
            chat_id=user_id,
            text="You need to add at least one resource before creating a subscription plan. Use /add_channel or /add_group to add resources.",
            reply_markup=create_back_button("admin:main")
        )
        return {"status": "error", "message": "No resources available"}
    
    # Provide instructions for creating a plan
    resources_list = "\n".join([f"- ID: {r.id}, Type: {'Channel' if r.type.value == 'channel' else 'Group'}, Chat ID: {r.tg_chat_id}" for r in resources])
    
    await telegram_api.send_message(
        chat_id=user_id,
        text=f"To create a new subscription plan, please use the following format:\n\n/create_plan_submit [name] [price] [duration_days] [resource_ids]\n\nExample:\n/create_plan_submit "Premium Plan" 9.99 30 1,2,3\n\nAvailable resources:\n{resources_list}",
        reply_markup=create_back_button("admin:manage_plans")
    )
    
    return {"status": "ok"}