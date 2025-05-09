from typing import List, Dict, Any, Optional, Union
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from app.models.models import SubscriptionPlan, PendingSubscription, TargetResource
from app.schemas.schemas import ResourceTypeEnum


def create_main_admin_menu() -> InlineKeyboardMarkup:
    """
    Creates the main admin menu with options for managing the bot.
    
    Returns:
        InlineKeyboardMarkup: The formatted keyboard markup for admin menu
    """
    keyboard = [
        [InlineKeyboardButton("Manage Plans", callback_data="admin:manage_plans")],
        [InlineKeyboardButton("Manage Resources", callback_data="admin:manage_resources")],
        [InlineKeyboardButton("Pending Subscriptions", callback_data="admin:pending_subs")],
        [InlineKeyboardButton("Broadcast Message", callback_data="admin:broadcast")],
        [InlineKeyboardButton("Bot Settings", callback_data="admin:settings")]
    ]
    
    return InlineKeyboardMarkup(keyboard)


def create_plan_selection_menu(plans: List[SubscriptionPlan]) -> InlineKeyboardMarkup:
    """
    Creates a menu for users to select a subscription plan.
    
    Args:
        plans: List of available subscription plans
        
    Returns:
        InlineKeyboardMarkup: The formatted keyboard markup for plan selection
    """
    keyboard = []
    
    for plan in plans:
        if plan.is_visible:
            button_text = f"{plan.name} ({plan.duration_days} days)"
            if plan.description:
                button_text += f" - {plan.description}"
            
            callback_data = f"select_plan:{plan.id}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
    
    # Add a cancel button
    keyboard.append([InlineKeyboardButton("Cancel", callback_data="cancel")])
    
    return InlineKeyboardMarkup(keyboard)


def create_resource_management_menu(resources: List[TargetResource]) -> InlineKeyboardMarkup:
    """
    Creates a menu for managing target resources (channels/groups).
    
    Args:
        resources: List of target resources to manage
        
    Returns:
        InlineKeyboardMarkup: The formatted keyboard markup for resource management
    """
    keyboard = []
    
    # Add resources
    for resource in resources:
        resource_type = "📢 Channel" if resource.type == ResourceTypeEnum.channel else "👥 Group"
        button_text = f"{resource_type}: {resource.tg_chat_id}"
        callback_data = f"resource:{resource.id}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
    
    # Add control buttons
    keyboard.append([
        InlineKeyboardButton("Add Resource", callback_data="resource:add"),
        InlineKeyboardButton("Back", callback_data="admin:main")
    ])
    
    return InlineKeyboardMarkup(keyboard)


def create_pending_subscription_menu(pending_subs: List[PendingSubscription]) -> InlineKeyboardMarkup:
    """
    Creates a menu for approving or rejecting pending subscriptions.
    
    Args:
        pending_subs: List of pending subscriptions
        
    Returns:
        InlineKeyboardMarkup: The formatted keyboard markup for subscription approval
    """
    keyboard = []
    
    for sub in pending_subs:
        # Display user and plan info
        button_text = f"User {sub.end_user_id} - Plan {sub.plan_id}"
        callback_data = f"view_pending:{sub.id}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
    
    # Add navigation button
    keyboard.append([InlineKeyboardButton("Back to Admin Menu", callback_data="admin:main")])
    
    return InlineKeyboardMarkup(keyboard)


def create_pending_subscription_action_menu(pending_sub_id: int) -> InlineKeyboardMarkup:
    """
    Creates action buttons for a specific pending subscription.
    
    Args:
        pending_sub_id: ID of the pending subscription
        
    Returns:
        InlineKeyboardMarkup: The formatted keyboard markup with approve/reject buttons
    """
    keyboard = [
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"admin_approve:{pending_sub_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"admin_reject:{pending_sub_id}")
        ],
        [InlineKeyboardButton("Back", callback_data="admin:pending_subs")]
    ]
    
    return InlineKeyboardMarkup(keyboard)


def create_settings_menu(config: Dict[str, Any]) -> InlineKeyboardMarkup:
    """
    Creates a menu for bot settings configuration.
    
    Args:
        config: Current bot configuration
        
    Returns:
        InlineKeyboardMarkup: The formatted keyboard markup for settings menu
    """
    keyboard = [
        [InlineKeyboardButton("Edit Welcome Message", callback_data="settings:welcome")],
        [InlineKeyboardButton("Edit Subscription Messages", callback_data="settings:subscription")],
        [InlineKeyboardButton("Edit Approval Messages", callback_data="settings:approval")],
        [InlineKeyboardButton("Payment Settings", callback_data="settings:payment")],
        [InlineKeyboardButton("Back to Admin Menu", callback_data="admin:main")]
    ]
    
    return InlineKeyboardMarkup(keyboard)


def create_broadcast_menu() -> InlineKeyboardMarkup:
    """
    Creates a menu for broadcast message options.
    
    Returns:
        InlineKeyboardMarkup: The formatted keyboard markup for broadcast options
    """
    keyboard = [
        [InlineKeyboardButton("Broadcast to All Subscribers", callback_data="broadcast:all")],
        [InlineKeyboardButton("Broadcast to Specific Plan", callback_data="broadcast:plan")],
        [InlineKeyboardButton("Cancel", callback_data="admin:main")]
    ]
    
    return InlineKeyboardMarkup(keyboard)


def create_confirmation_menu(action: str, entity_id: int) -> InlineKeyboardMarkup:
    """
    Creates a confirmation menu with Yes/No options.
    
    Args:
        action: The action to confirm (e.g., 'delete_plan')
        entity_id: ID of the entity to perform action on
        
    Returns:
        InlineKeyboardMarkup: The formatted keyboard markup for confirmation
    """
    keyboard = [
        [
            InlineKeyboardButton("Yes", callback_data=f"{action}_confirm:{entity_id}"),
            InlineKeyboardButton("No", callback_data=f"{action}_cancel:{entity_id}")
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)


def create_back_button(callback_data: str = "admin:main") -> InlineKeyboardMarkup:
    """
    Creates a simple back button.
    
    Args:
        callback_data: The callback data for the back button
        
    Returns:
        InlineKeyboardMarkup: The formatted keyboard markup with a back button
    """
    keyboard = [[InlineKeyboardButton("Back", callback_data=callback_data)]]
    return InlineKeyboardMarkup(keyboard)


def create_payment_methods_menu(payment_methods: List[str]) -> InlineKeyboardMarkup:
    """
    Creates a menu for managing payment methods with add/remove buttons.
    
    Args:
        payment_methods: List of currently configured payment methods
        
    Returns:
        InlineKeyboardMarkup: The formatted keyboard markup for payment methods management
    """
    keyboard = []
    
    # Display current payment methods with remove buttons
    for method in payment_methods:
        keyboard.append([
            InlineKeyboardButton(f"{method}", callback_data=f"payment_method_info:{method}"),
            InlineKeyboardButton("❌ Remove", callback_data=f"remove_payment_method:{method}")
        ])
    
    # Add a button to add new payment method
    keyboard.append([InlineKeyboardButton("➕ Add Payment Method", callback_data="add_payment_method")])
    
    # Add back button
    keyboard.append([InlineKeyboardButton("Back", callback_data="admin:settings")])
    
    return InlineKeyboardMarkup(keyboard)