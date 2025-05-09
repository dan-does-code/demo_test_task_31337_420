from app.models.base import Base, engine
from app.models.models import PlatformUser, ManagedBot, SubscriptionPlan, TargetResource, EndUser, Subscription, PendingSubscription


def init_db():
    """Initialize database tables"""
    # Create all tables
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")