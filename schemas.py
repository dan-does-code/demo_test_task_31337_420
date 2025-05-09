from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum


class SubscriptionStatusEnum(str, Enum):
    active = "active"
    expired = "expired"


class PendingSubscriptionStatusEnum(str, Enum):
    pending_approval = "pending_approval"
    approved = "approved"
    rejected = "rejected"


class ResourceTypeEnum(str, Enum):
    channel = "channel"
    group = "group"


class InviteLinkTypeEnum(str, Enum):
    unique = "unique"
    static = "static"
    request = "request"
    custom = "custom"


# Base schemas
class PlatformUserBase(BaseModel):
    tg_user_id: int


class ManagedBotBase(BaseModel):
    platform_user_id: int
    username: str
    config_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    intended_payment_methods: Optional[List[str]] = Field(default_factory=list)
    webhook_secret: Optional[str] = None


class SubscriptionPlanBase(BaseModel):
    managed_bot_id: int
    name: str
    duration_days: int
    linked_resource_ids: List[int] = Field(default_factory=list)
    is_visible: bool = True
    description: Optional[str] = None


class TargetResourceBase(BaseModel):
    managed_bot_id: int
    tg_chat_id: int
    type: ResourceTypeEnum
    invite_link_type: InviteLinkTypeEnum
    custom_link: Optional[str] = None
    is_mandatory: bool = False


class EndUserBase(BaseModel):
    tg_user_id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None


class SubscriptionBase(BaseModel):
    end_user_id: int
    managed_bot_id: int
    plan_id: int
    start_date: datetime
    end_date: datetime
    status: SubscriptionStatusEnum = SubscriptionStatusEnum.active


class PendingSubscriptionBase(BaseModel):
    end_user_id: int
    managed_bot_id: int
    plan_id: int
    status: PendingSubscriptionStatusEnum = PendingSubscriptionStatusEnum.pending_approval


# Create schemas
class PlatformUserCreate(PlatformUserBase):
    pass


class ManagedBotCreate(ManagedBotBase):
    tg_token: str  # Will be encrypted before storage


class SubscriptionPlanCreate(SubscriptionPlanBase):
    pass


class TargetResourceCreate(TargetResourceBase):
    pass


class EndUserCreate(EndUserBase):
    pass


class SubscriptionCreate(BaseModel):
    end_user_id: int
    managed_bot_id: int
    plan_id: int


class PendingSubscriptionCreate(BaseModel):
    end_user_id: int
    managed_bot_id: int
    plan_id: int


# Update schemas
class PlatformUserUpdate(BaseModel):
    tg_user_id: Optional[int] = None


class ManagedBotUpdate(BaseModel):
    platform_user_id: Optional[int] = None
    tg_token: Optional[str] = None  # Will be encrypted before storage
    username: Optional[str] = None
    config_data: Optional[Dict[str, Any]] = None
    intended_payment_methods: Optional[List[str]] = None
    webhook_secret: Optional[str] = None


class SubscriptionPlanUpdate(BaseModel):
    managed_bot_id: Optional[int] = None
    name: Optional[str] = None
    duration_days: Optional[int] = None
    linked_resource_ids: Optional[List[int]] = None
    is_visible: Optional[bool] = None
    description: Optional[str] = None


class TargetResourceUpdate(BaseModel):
    managed_bot_id: Optional[int] = None
    tg_chat_id: Optional[int] = None
    type: Optional[ResourceTypeEnum] = None
    invite_link_type: Optional[InviteLinkTypeEnum] = None
    custom_link: Optional[str] = None
    is_mandatory: Optional[bool] = None


class EndUserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None


class SubscriptionUpdate(BaseModel):
    end_user_id: Optional[int] = None
    managed_bot_id: Optional[int] = None
    plan_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[SubscriptionStatusEnum] = None


class PendingSubscriptionUpdate(BaseModel):
    status: Optional[PendingSubscriptionStatusEnum] = None


# Response schemas
class PlatformUserResponse(PlatformUserBase):
    id: int

    class Config:
        orm_mode = True


class ManagedBotResponse(ManagedBotBase):
    id: int

    class Config:
        orm_mode = True


class SubscriptionPlanResponse(SubscriptionPlanBase):
    id: int

    class Config:
        orm_mode = True


class TargetResourceResponse(TargetResourceBase):
    id: int

    class Config:
        orm_mode = True


class EndUserResponse(EndUserBase):
    class Config:
        orm_mode = True


class SubscriptionResponse(SubscriptionBase):
    id: int

    class Config:
        orm_mode = True


class PendingSubscriptionResponse(PendingSubscriptionBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


# Telegram webhook schemas
class TelegramUser(BaseModel):
    id: int
    is_bot: bool
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None


class TelegramChat(BaseModel):
    id: int
    type: str
    title: Optional[str] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class TelegramMessage(BaseModel):
    message_id: int
    from_user: Optional[TelegramUser] = Field(None, alias="from")
    chat: TelegramChat
    date: int
    text: Optional[str] = None

    class Config:
        allow_population_by_field_name = True


class TelegramCallbackQuery(BaseModel):
    id: str
    from_user: TelegramUser = Field(..., alias="from")
    message: Optional[TelegramMessage] = None
    data: Optional[str] = None

    class Config:
        allow_population_by_field_name = True


class TelegramUpdate(BaseModel):
    update_id: int
    message: Optional[TelegramMessage] = None
    callback_query: Optional[TelegramCallbackQuery] = None


# Config schemas
class BotConfigUpdate(BaseModel):
    welcome_message: Optional[str] = None
    subscription_message: Optional[str] = None
    expired_message: Optional[str] = None
    pending_message: Optional[str] = None
    approved_message: Optional[str] = None
    rejected_message: Optional[str] = None
    custom_settings: Optional[Dict[str, Any]] = None


# Broadcast schemas
class BroadcastRequest(BaseModel):
    managed_bot_id: int
    message_text: str
    target_user_ids: Optional[List[int]] = None  # If None, broadcast to all subscribers