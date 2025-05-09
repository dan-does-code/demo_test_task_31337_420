# Telegram Paywall Bot Constructor - Project [Your Project Codename/Name]

**Version:** 0.3 (Pre-Refactor)
**Date:** [Current Date]
**Lead/Contact:** [Your Name/Contact]

## 1. Overview

This project aims to build a **Telegram Bot Constructor platform** (similar in concept to Admaker Bot). The platform will enable users (let's call them "Bot Creators") to easily create, configure, and manage their own Telegram bots. The primary function of these created bots will be to act as **paywalls**, managing paid subscriptions for access to private Telegram channels, groups, or other digital content/services offered via Telegram.

The core value proposition is to provide a no-code/low-code solution for individuals and businesses to monetize their Telegram presence.

## 2. Core Concept & Purpose

Many content creators, community managers, and businesses use Telegram to deliver value. This platform will empower them to:

*   **Monetize Content:** Easily set up paid access to exclusive channels/groups.
*   **Automate Subscriptions:** Automate the process of granting and revoking access based on payment status.
*   **Manage Communities:** Provide tools for managing subscribers and understanding basic analytics.
*   **No Programming Required (for Bot Creators):** The entire bot creation and management process should be doable through a user-friendly interface (initially, this interface will be the main platform bot itself).

## 3. Key Features (Target End-State)

### 3.1. For Bot Creators (Platform Users):

*   **Bot Creation:**
    *   Ability to register their existing bot tokens (obtained from @BotFather) with our platform.
    *   (Future) Guided creation if technically feasible.
*   **Subscription Plan Management:**
    *   Define multiple subscription plans (e.g., Bronze, Silver, Gold).
    *   Set plan details: name, description, duration (e.g., 7 days, 30 days, 365 days, lifetime), and price.
    *   Visibility control for plans (e.g., public, unlisted).
*   **Target Resource Management:**
    *   Link subscription plans to one or more target Telegram channels/groups.
    *   Specify access method per resource (e.g., generate unique invite link, approve join request, provide static link).
*   **Payment Gateway Integration (The "Socket" Concept):**
    *   Bot Creators will need to connect their *own* accounts from supported payment gateways (e.g., Stripe, Crypto Processors). Our platform facilitates the connection and triggers payments *to their accounts*, potentially taking a commission.
    *   The platform should NOT hold the Bot Creator's payment gateway credentials directly if OAuth or similar secure methods are available.
*   **Customization:**
    *   Customize bot messages (welcome, payment instructions, success, expiry warnings).
    *   Language settings for their created bot.
*   **Subscriber Management:**
    *   View active subscribers, their plans, and expiry dates.
    *   Manually add/remove/extend subscriptions (for exceptions).
    *   Block/unblock end-users.
*   **Basic Analytics:**
    *   View subscriber counts.
    *   (Future) Basic revenue insights (from confirmed payments).
*   **Broadcasting:** Send messages to all active subscribers of a specific plan or bot.
*   **Admin Interface:** All the above features should be manageable through an intuitive interface, likely the main platform bot initially for the Bot Creator.

### 3.2. For End Users (Subscribers of Created Bots):

*   Clear `/start` message explaining the bot's purpose.
*   Ability to view available subscription plans.
*   Intuitive process to select a plan and initiate payment.
*   Receive confirmation and access (e.g., invite link) upon successful payment.
*   Check their current subscription status and expiry date.
*   Receive notifications for subscription expiry.

### 3.3. For Platform Administrator (You/Us):

*   Oversee all created bots and platform users.
*   Manage platform-level settings.
*   (Future) System-wide analytics and user support tools.

## 4. High-Level Architecture (Target)

The system should be designed as a multi-tenant application.

+-------------------------+ +-----------------------+ +---------------------+
| Telegram Bot API |<--->| Platform Webhook/ |<--->| Request Router |
| (for ALL managed bots) | | Polling Endpoint | | (Identifies Target Bot|
+-------------------------+ +-----------------------+ | & User Type) |
+----------+----------+
|
+-----------------------------+-----------------------------+
| |
+-------------V-------------+ +-------------V-------------+
| Bot Creator Logic | | End User Logic |
| (Admin Menu in their bot) | | (Interaction in their bot) |
+-------------+-------------+ +-------------+-------------+
| |
| +--------------------------+ |
| | Configuration Service |<----------------------------+
| | (CRUD for Plans, Bots, |
| | Resources, Settings) |
| +------------+-------------+
| |
| +------------V-------------+ +--------------------------+
+->| Subscription Manager |<--->| Access Granter |
| (CRUD for Subscriptions, | | (Generates/Sends Links, |
| Pending Subs) | | Approves Join Requests) |
+------------+-------------+ +------------+-------------+
| |
+-------------------------------+ +----------------+
| |
+----------------------V-+ +------------------------+ +--------------------------V-+ +------------------V---+
| Payment Socket: |<-- | Payment Socket: |<-- | Payment Socket: | | Telegram API |
| Initiate (End User) | | Webhook Handler | | Confirm (Manual/Webhook) | | Wrapper (for this |
| | | (from Payment Gateway) | | | | specific ManagedBot|
+----------------------+ +------------------------+ +--------------------------+ +--------------------+
+-------------------------+ +--------------------------+
| Database (PostgreSQL) |<--->| Task Queue & Scheduler |
| (Users, Bots, Plans, | | (e.g., Redis, Celery/ |
| Subs, Resources, etc.) | | APScheduler for Expiry) |
+-------------------------+ +--------------------------+


*   **Webhook/Polling Endpoint:** A single, central endpoint (or polling mechanism) receives all updates for all bots managed by the platform.
*   **Request Router:** Identifies which `ManagedBot` the update is for and whether the interacting user is the `BotCreator` (admin for that bot) or an `EndUser`.
*   **Configuration Service:** Handles CRUD operations for bot settings, plans, resources.
*   **Subscription Manager:** Manages the lifecycle of subscriptions (pending, active, expired).
*   **Access Granter:** Responsible for providing access to resources (e.g., generating invite links, approving join requests) via the `Telegram API Wrapper`.
*   **Payment Sockets (Crucial Design Pattern):**
    *   `Payment Socket: Initiate`: Called when an `EndUser` selects a plan. In the current refactor target, this will create a `PendingSubscription` and notify the `BotCreator` for manual approval. *Future:* This is where integration with payment gateways to generate payment links will occur.
    *   `Payment Socket: Confirm`: Called when a payment is confirmed. Currently, this will be triggered manually by the `BotCreator`. *Future:* This will primarily be triggered by the `Payment Socket: Webhook Handler`.
    *   `Payment Socket: Webhook Handler`: A placeholder endpoint that will eventually receive and validate webhooks from payment gateways, then trigger the `Confirm` socket.
*   **Database:** Stores all platform data (platform users, managed bots, plans, resources, end-users, subscriptions, etc.).
*   **Task Queue & Scheduler:** For background tasks like checking for expired subscriptions and revoking access.
*   **Telegram API Wrapper:** An abstraction layer for interacting with the Telegram Bot API, handling rate limits and specific bot tokens.

## 5. Core User Flows (Simplified)

1.  **Bot Creator - Onboarding & Setup:**
    1.  Platform Admin adds Bot Creator's `telegram_user_id` (or they register).
    2.  Bot Creator starts the main platform bot.
    3.  Goes to "Manage My Bots" -> "Add New Bot" -> Provides Bot Token.
    4.  Selects the newly added bot to configure it.
    5.  Creates `SubscriptionPlan`(s): name, duration (no price yet in manual mode).
    6.  Adds `TargetResource`(s): provides channel/group ID.
    7.  Links `SubscriptionPlan`(s) to `TargetResource`(s).
    8.  Sets welcome messages, etc.
    9.  The created bot is now ready for End Users.

2.  **End User - Subscription (Manual Approval Flow):**
    1.  End User finds and starts a `ManagedBot`.
    2.  Bot displays available `SubscriptionPlan`(s).
    3.  End User selects a plan.
    4.  `Payment Socket: Initiate` is triggered:
        *   A `PendingSubscription` record is created (status: `pending_approval`).
        *   End User is notified: "Your request for [Plan Name] is pending admin approval."
        *   Bot Creator is notified: "[User X] requested [Plan Name] for bot [Bot Y]. Approve in Admin Menu."
    5.  Bot Creator goes to their bot's Admin Menu -> "Pending Activations".
    6.  Selects the pending request and clicks "Approve."
    7.  `Payment Socket: Confirm` is triggered:
        *   `AccessGranter` creates an `Subscription` record (active status, start/end dates).
        *   `AccessGranter` generates invite link(s) / approves join request(s).
        *   End User receives the link(s)/confirmation and the plan's welcome message.
        *   `PendingSubscription` status updated to `approved`.

3.  **Subscription Expiry:**
    1.  Scheduled task (`Expiry_Processor`) runs periodically.
    2.  Identifies `Subscription` records where `end_date` has passed and status is `active`.
    3.  For each, uses `Telegram API Wrapper` to kick the `EndUser` from linked `TargetResource`(s).
    4.  Updates `Subscription` status to `expired`.
    5.  (Optional) Notifies `EndUser` of expiry.

## 6. Technology Stack (Current/Intended)

*   **Language:** Python 3.10+
*   **Telegram Framework:** Aiogram 3.x
*   **Database ORM:** SQLAlchemy 2.x (with asyncio support)
*   **Database:** PostgreSQL (preferred for production), SQLite (for development/simplicity initially)
*   **Async Driver:** `asyncpg` (for PostgreSQL), `aiosqlite` (for SQLite)
*   **Task Scheduling:** APScheduler
*   **FSM Storage:** Aiogram's `MemoryStorage` (initially), Redis (for scalability)
*   **Configuration:** `python-dotenv`, `pydantic-settings`
*   **(Future Web Dashboard):** FastAPI/Django + React/Vue

## 7. Database Schema (Key Entities - Refer to `db/models.py`)

*   `PlatformUser`: Users who can create/manage bots on our platform (initially, just the main admin).
*   `ManagedBot`: Represents a Telegram bot created and managed by a `PlatformUser` via our system. Stores its token, config, etc.
*   `SubscriptionPlan`: Defines a subscription offering (name, duration, linked resources).
*   `TargetResource`: A Telegram channel or group linked to a `SubscriptionPlan`.
*   `EndUser`: An end-user interacting with a `ManagedBot` (potential or actual subscriber).
*   `Subscription`: An active or past subscription record for an `EndUser` to a `SubscriptionPlan`.
*   `PendingSubscription`: A record for subscription requests awaiting payment/approval.
*   `PlanResourceLink`: Association table for many-to-many between plans and resources.

## 8. Current Status (approx. 30% complete) & Refactoring Goals

The current codebase has foundational elements but suffers from:

*   **Incomplete Multi-Bot Handling:** The logic for managing multiple `ManagedBot` instances simultaneously (dispatching updates, using correct tokens) is not robust or is missing. The current `BotContextMiddleware` is a starting point but needs significant work.
*   **State Management Complexity:** FSM states might be overly complex or not cleanly implemented.
*   **Scalability Concerns:** Current single-process, polling-based approach for the main bot won't scale.
*   **Tight Coupling:** Some modules might be too tightly coupled, making changes difficult.
*   **Inconsistent Error Handling.**
*   **"Payment Sockets" Not Fully Abstracted:** While the idea exists, the separation might not be clean enough for easy future payment gateway integration.
*   **Incomplete Features:** Many admin and user-facing features (plan editing, resource management, full settings customization, user status) are placeholders or not implemented.

**Refactoring Goals:**

1.  **Solidify Multi-Bot Architecture:**
    *   Establish a clear and scalable way to handle updates for *all* `ManagedBot`s. This might involve dynamic `Bot` instance creation and a master dispatcher, or a webhook-based router.
    *   Ensure `BotContextMiddleware` (or equivalent) reliably provides the correct `ManagedBot` context (DB model and `aiogram.Bot` instance) to handlers.
2.  **Cleanly Implement "Payment Sockets":** Ensure the `initiate`, `confirm`, and `webhook_handler` sockets are well-defined interfaces, with the current manual approval flow being one implementation of the `confirm` path.
3.  **Modular Design:** Improve separation of concerns between services (configuration, subscription, access granting).
4.  **Robust State Management (FSM):** Simplify and clarify FSM usage for admin configuration flows.
5.  **Scalable Background Tasks:** Ensure `Expiry_Processor` and any future background tasks are designed for scalability.
6.  **Complete Core CRUD Functionality:** Implement all necessary CRUD operations for plans, resources, and bot settings through the admin interface.
7.  **Improve User Experience:** Ensure both Bot Creator and End User flows are intuitive.
8.  **Comprehensive Error Handling and Logging.**
9.  **Prepare for Actual Payment Integration:** The refactored code should make it straightforward to plug in real payment gateway logic into the defined sockets.

## 9. Project Setup (Current)

1.  Clone the repository.
2.  Create a virtual environment: `python -m venv venv && source venv/bin/activate`
3.  Install dependencies: `pip install -r requirements.txt`
4.  Create a `.env` file based on `.env.example` (if exists) or the following:
    ```env
    BOT_TOKEN="YOUR_MAIN_PLATFORM_BOT_TOKEN"
    PLATFORM_ADMIN_ID="YOUR_TELEGRAM_USER_ID"
    DATABASE_URL="sqlite+aiosqlite:///./app.db" # Or your PostgreSQL DSN
    ```
5.  Initialize the database (if first time, or after schema changes):
    *   The `main.py` script attempts to run `init_db()`.
6.  Run the main application: `python main.py`

## 10. Key Challenges to Address in Refactor

*   **Securely Managing Bot Tokens:** How to store and use tokens for many managed bots.
*   **Telegram API Rate Limits:** Implementing graceful handling across multiple bot operations.
*   **Atomicity and Reliability:** Ensuring subscription granting/revoking is reliable, especially around payment confirmations.
*   **User Experience for Bot Creators:** Making the bot-based admin interface powerful yet easy to use.

---

This README should provide a comprehensive overview for the programmer to understand the project's intent and the direction for the refactor. Good luck!
