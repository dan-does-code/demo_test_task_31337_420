from sqlalchemy import Column, Integer, String, BigInteger, ForeignKey, Boolean, DateTime, Text, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base
import enum


class SubscriptionStatus(enum.Enum):
    active = "active"
    expired = "expired"


class PendingSubscriptionStatus(enum.Enum):
    pending_approval = "pending_approval"
    approved = "approved"
    rejected = "rejected"


class ResourceType(enum.Enum):
    channel = "channel"
    group = "group"


class InviteLinkType(enum.Enum):
    unique = "unique"
    static = "static"
    request = "request"
    custom = "custom"


class PlatformUser(Base):
    __tablename__ = "platform_users"

    id = Column(Integer, primary_key=True, index=True)
    tg_user_id = Column(BigInteger, unique=True, index=True)
    
    # Relationships
    managed_bots = relationship("ManagedBot", back_populates="platform_user")


class ManagedBot(Base):
    __tablename__ = "managed_bots"

    id = Column(Integer, primary_key=True, index=True)
    platform_user_id = Column(Integer, ForeignKey("platform_users.id"))
    tg_token_encrypted = Column(String)
    username = Column(String)
    config_data = Column(JSON)
    intended_payment_methods = Column(JSON)
    webhook_secret = Column(String, unique=True, index=True)
    
    # Relationships
    platform_user = relationship("PlatformUser", back_populates="managed_bots")
    subscription_plans = relationship("SubscriptionPlan", back_populates="managed_bot")
    target_resources = relationship("TargetResource", back_populates="managed_bot")
    subscriptions = relationship("Subscription", back_populates="managed_bot")
    pending_subscriptions = relationship("PendingSubscription", back_populates="managed_bot")


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id = Column(Integer, primary_key=True, index=True)
    managed_bot_id = Column(Integer, ForeignKey("managed_bots.id"))
    name = Column(String)
    duration_days = Column(Integer)
    linked_resource_ids = Column(JSON)  # List of target resource IDs
    is_visible = Column(Boolean, default=True)
    description = Column(Text)
    
    # Relationships
    managed_bot = relationship("ManagedBot", back_populates="subscription_plans")
    subscriptions = relationship("Subscription", back_populates="plan")
    pending_subscriptions = relationship("PendingSubscription", back_populates="plan")


class TargetResource(Base):
    __tablename__ = "target_resources"

    id = Column(Integer, primary_key=True, index=True)
    managed_bot_id = Column(Integer, ForeignKey("managed_bots.id"))
    tg_chat_id = Column(BigInteger)
    type = Column(Enum(ResourceType))
    invite_link_type = Column(Enum(InviteLinkType))
    custom_link = Column(Text, nullable=True)
    is_mandatory = Column(Boolean, default=False)
    
    # Relationships
    managed_bot = relationship("ManagedBot", back_populates="target_resources")


class EndUser(Base):
    __tablename__ = "end_users"

    tg_user_id = Column(BigInteger, primary_key=True, index=True)
    first_name = Column(String)
    last_name = Column(String, nullable=True)
    username = Column(String, nullable=True)
    
    # Relationships
    subscriptions = relationship("Subscription", back_populates="end_user")
    pending_subscriptions = relationship("PendingSubscription", back_populates="end_user")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    end_user_id = Column(BigInteger, ForeignKey("end_users.tg_user_id"))
    managed_bot_id = Column(Integer, ForeignKey("managed_bots.id"))
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"))
    start_date = Column(DateTime, default=func.now())
    end_date = Column(DateTime)
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.active)
    
    # Relationships
    end_user = relationship("EndUser", back_populates="subscriptions")
    managed_bot = relationship("ManagedBot", back_populates="subscriptions")
    plan = relationship("SubscriptionPlan", back_populates="subscriptions")


class PendingSubscription(Base):
    __tablename__ = "pending_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    end_user_id = Column(BigInteger, ForeignKey("end_users.tg_user_id"))
    managed_bot_id = Column(Integer, ForeignKey("managed_bots.id"))
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"))
    created_at = Column(DateTime, default=func.now())
    status = Column(Enum(PendingSubscriptionStatus), default=PendingSubscriptionStatus.pending_approval)
    
    # Relationships
    end_user = relationship("EndUser", back_populates="pending_subscriptions")
    managed_bot = relationship("ManagedBot", back_populates="pending_subscriptions")
    plan = relationship("SubscriptionPlan", back_populates="pending_subscriptions")