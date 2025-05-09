
```markdown
# Telegram Paywall Bot Constructor - Project [Your Project Codename/Name]

**Version:** 0.3.5 (Pre-Refactor, Stars Integration Planned)
**Date:** [Current Date]
**Lead/Contact:** [Your Name/Contact]

## 1. Overview

This project aims to build a **Telegram Bot Constructor platform** (similar in concept to Admaker Bot). The platform will enable users (let's call them "Bot Creators") to easily create, configure, and manage their own Telegram bots. The primary function of these created bots will be to act as **paywalls**, managing paid subscriptions for access to private Telegram channels, groups, or other digital content/services offered via Telegram.

The core value proposition is to provide a no-code/low-code solution for individuals and businesses to monetize their Telegram presence.

## 2. Core Concept & Purpose

Many content creators, community managers, and businesses use Telegram to deliver value. This platform will empower them to:

*   **Monetize Content:** Easily set up paid access to exclusive channels/groups using various payment methods, **including the native Telegram Stars**.
*   **Automate Subscriptions:** Automate the process of granting and revoking access based on payment status.
*   **Manage Communities:** Provide tools for managing subscribers and understanding basic analytics.
*   **No Programming Required (for Bot Creators):** The entire bot creation and management process should be doable through a user-friendly interface (initially, this interface will be the main platform bot itself).

## 3. Key Features (Target End-State)

### 3.1. For Bot Creators (Platform Users):

*   **Bot Creation:**
    *   Ability to register their existing bot tokens (obtained from @BotFather) with our platform.
*   **Subscription Plan Management:**
    *   Define multiple subscription plans (e.g., Bronze, Silver, Gold).
    *   Set plan details: name, description, duration (e.g., 7 days, 30 days, 365 days, lifetime).
    *   **Pricing:**
        *   Set prices in **Telegram Stars (XTR)** for each plan.
        *   (Future) Set prices in fiat currencies for integration with external payment gateways.
    *   Visibility control for plans (e.g., public, unlisted).
*   **Target Resource Management:**
    *   Link subscription plans to one or more target Telegram channels/groups.
    *   Specify access method per resource (e.g., generate unique invite link, approve join request, provide static link).
*   **Payment Method Configuration:**
    *   **Telegram Stars Integration:**
        *   Enable/disable Stars payments for their bot (no external API keys needed). Bot Creators' bots will collect Stars directly.
        *   View successful Stars transactions and their `telegram_payment_charge_id`.
        *   Initiate refunds for Stars payments via the platform interface.
    *   **(Future) External Payment Gateway Integration (The "Socket" Concept):**
        *   Bot Creators will connect their *own* accounts from supported payment gateways (e.g., Stripe, CryptoBot). Our platform facilitates the connection and triggers payments *to their accounts*, potentially taking a commission.
*   **Customization:**
    *   Customize bot messages (welcome, payment instructions, success, expiry warnings).
    *   Customize the `/paysupport` command response for their bot, as required by Telegram for Stars payments.
    *   Language settings for their created bot.
*   **Subscriber Management:**
    *   View active subscribers, their plans, and expiry dates.
    *   Manually add/remove/extend subscriptions (for exceptions).
    *   Block/unblock end-users.
*   **Basic Analytics:**
    *   View subscriber counts.
    *   (Future) Basic revenue insights (from confirmed payments across different methods).
*   **Broadcasting:** Send messages to all active subscribers of a specific plan or bot.
*   **Admin Interface:** All the above features should be manageable through an intuitive interface, likely the main platform bot initially for the Bot Creator.

### 3.2. For End Users (Subscribers of Created Bots):

*   Clear `/start` message explaining the bot's purpose.
*   Ability to view available subscription plans and their prices (e.g., in Stars).
*   Intuitive process to select a plan and initiate payment:
    *   **For Telegram Stars:** A native Telegram payment window will appear.
    *   **(Future) For other gateways:** Redirected to the gateway or presented with payment details.
*   Receive confirmation and access (e.g., invite link) upon successful payment.
*   Check their current subscription status and expiry date.
*   Receive notifications for subscription expiry.
*   Access to a `/paysupport` command providing refund/support information.

### 3.3. For Platform Administrator (You/Us):

*   Oversee all created bots and platform users.
*   Manage platform-level settings.
*   (Future) System-wide analytics and user support tools.

## 4. High-Level Architecture (Target)

The system should be designed as a multi-tenant application.

```
+-------------------------+     +-----------------------+     +---------------------+
| Telegram Bot API        |<--->| Platform Webhook/     |<--->| Request Router      |
| (for ALL managed bots,  |     | Polling Endpoint      |     | (Identifies Target Bot|
| including Stars payment |     +-----------------------+     | & User Type)        |
| events like             |                                   +----------+----------+
| PreCheckoutQuery &      |                                              |
| SuccessfulPayment)      |              +-----------------------------+-----------------------------+
+-------------------------+              |                                                           |
                               +-------------V-------------+                               +-------------V-------------+
                               | Bot Creator Logic           |                               | End User Logic              |
                               | (Admin Menu in their bot)   |                               | (Interaction in their bot)  |
                               +-------------+-------------+                               +-------------+-------------+
                                             |                                                           |
                                             |  +--------------------------+                             |
                                             |  | Configuration Service    |<----------------------------+
                                             |  | (CRUD for Plans, Bots,   |
                                             |  | Resources, Settings)     |
                                             |  +------------+-------------+
                                             |               |
                                             |  +------------V-------------+     +--------------------------+
                                             +->| Subscription Manager     |<--->| Access Granter           |
                                                | (CRUD for Subscriptions, |     | (Generates/Sends Links,  |
                                                | Pending Subs)            |     | Approves Join Requests)  |
                                                +------------+-------------+     +------------+-------------+
                                                             |                                |
                             +-------------------------------+                                +----------------+
                             |                                                                                 |
  +----------------------V-+   +------------------------+   +--------------------------V-+  +------------------V---+
  | Payment Socket:      |<-- | Payment Socket:        |<-- | Payment Socket:          |  | Telegram API       |
  | Initiate (End User)  |    | Webhook Handler        |    | Confirm (Manual/Webhook/ |  | Wrapper (for this  |
  | (Triggers Stars inv. |    | (from Payment Gateway) |    | SuccessfulPayment event) |  | specific ManagedBot|
  | or other gateways)   |    +------------------------+    +--------------------------+  +--------------------+
  +----------------------+

+-------------------------+     +--------------------------+
| Database (PostgreSQL)   |<--->| Task Queue & Scheduler   |
| (Users, Bots, Plans,    |     | (e.g., Redis, Celery/    |
| Subs, Resources, etc.)  |     | APScheduler for Expiry)  |
+-------------------------+     +--------------------------+
```

*   **Webhook/Polling Endpoint:** A single, central endpoint (or polling mechanism) receives all updates for all bots managed by the platform. This includes standard messages, callbacks, and **Telegram payment events (`PreCheckoutQuery`, `Message` with `SuccessfulPayment`)**.
*   **Request Router:** Identifies which `ManagedBot` the update is for and whether the interacting user is the `BotCreator` (admin for that bot) or an `EndUser`. For payment events, it routes them to dedicated payment handlers.
*   **Configuration Service:** Handles CRUD operations for bot settings, plans (including Stars pricing), resources.
*   **Subscription Manager:** Manages the lifecycle of subscriptions (pending, active, expired).
*   **Access Granter:** Responsible for providing access to resources (e.g., generating invite links, approving join requests) via the `Telegram API Wrapper`.
*   **Payment Sockets & Handlers (Crucial Design Pattern):**
    *   `Payment Socket: Initiate`: Called when an `EndUser` selects a plan.
        *   **For Stars:** Triggers `bot.answer_invoice()` with "XTR" currency and an empty `provider_token`.
        *   **(Future) For other gateways:** Calls the respective gateway's API.
    *   **Dedicated Telegram Payment Handlers:**
        *   `PreCheckoutQuery` handler: Validates the payment request and responds with `ok=True` or `ok=False`.
        *   `SuccessfulPayment` handler (for `Message` with `F.successful_payment`): Triggered after a successful Stars payment. This internally calls the `Payment Socket: Confirm` logic.
    *   `Payment Socket: Confirm`: Called when a payment is confirmed (manually by Bot Creator, by a `SuccessfulPayment` event for Stars, or by a webhook for external gateways).
    *   `(Future) Payment Socket: Webhook Handler`: An endpoint that will receive and validate webhooks from external payment gateways (like CryptoBot), then trigger the `Confirm` socket.
*   **Database:** Stores all platform data (platform users, managed bots, plans with Stars prices, resources, end-users, subscriptions with payment details like `telegram_payment_charge_id`, etc.).
*   **Task Queue & Scheduler:** For background tasks like checking for expired subscriptions and revoking access.
*   **Telegram API Wrapper:** An abstraction layer for interacting with the Telegram Bot API, handling rate limits and specific bot tokens. This wrapper will be used for sending invoices, answering pre-checkout queries, and refunding Stars.

## 5. Core User Flows (Simplified)

1.  **Bot Creator - Onboarding & Setup (with Stars):**
    1.  Platform Admin adds Bot Creator's `telegram_user_id` (or they register).
    2.  Bot Creator starts the main platform bot.
    3.  Goes to "Manage My Bots" -> "Add New Bot" -> Provides Bot Token.
    4.  Selects the newly added bot to configure it.
    5.  Navigates to "Payment Settings" -> Enables "Telegram Stars."
    6.  Creates `SubscriptionPlan`(s): name, duration, **price in Stars**.
    7.  Adds `TargetResource`(s): provides channel/group ID.
    8.  Links `SubscriptionPlan`(s) to `TargetResource`(s).
    9.  Sets welcome messages, **customizes `/paysupport` text**.
    10. The created bot is now ready for End Users to pay with Stars.

2.  **End User - Subscription (Telegram Stars Flow):**
    1.  End User finds and starts a `ManagedBot`.
    2.  Bot displays available `SubscriptionPlan`(s) showing prices in ⭐️.
    3.  End User selects a plan.
    4.  `Payment Socket: Initiate` is triggered: `ManagedBot` sends an invoice (`answer_invoice`) for Stars payment.
    5.  Telegram client shows a payment confirmation dialog to the End User.
    6.  If End User proceeds, Telegram sends a `PreCheckoutQuery` to the `ManagedBot`.
    7.  Platform's `PreCheckoutQuery` handler (for that `ManagedBot`) validates and responds `ok=True`.
    8.  End User confirms payment in the Telegram dialog.
    9.  Telegram processes the payment. If successful, sends a `Message` with `successful_payment` data to the `ManagedBot`.
    10. Platform's `SuccessfulPayment` handler (for that `ManagedBot`):
        *   Parses `invoice_payload` and `successful_payment` data (including `telegram_payment_charge_id`).
        *   Internally calls `Payment Socket: Confirm` logic.
        *   `AccessGranter` creates an `Subscription` record (active status, start/end dates, stores Stars payment details).
        *   `AccessGranter` generates invite link(s) / approves join request(s).
        *   End User receives the link(s)/confirmation and the plan's welcome message.
        *   (Optional) `PendingSubscription` status updated/deleted.

3.  **Subscription Expiry:** (Same as before)
    1.  Scheduled task (`Expiry_Processor`) runs periodically.
    2.  Identifies `Subscription` records where `end_date` has passed and status is `active`.
    3.  For each, uses `Telegram API Wrapper` to kick the `EndUser` from linked `TargetResource`(s).
    4.  Updates `Subscription` status to `expired`.
    5.  (Optional) Notifies `EndUser` of expiry.

## 6. Technology Stack (Current/Intended)

*   **Language:** Python 3.10+
*   **Telegram Framework:** Aiogram **3.7.0+** (for Telegram Stars support)
*   **Database ORM:** SQLAlchemy 2.x (with asyncio support)
*   **Database:** PostgreSQL (preferred for production), SQLite (for development/simplicity initially)
*   **Async Driver:** `asyncpg` (for PostgreSQL), `aiosqlite` (for SQLite)
*   **Task Scheduling:** APScheduler
*   **FSM Storage:** Aiogram's `MemoryStorage` (initially), Redis (for scalability)
*   **Configuration:** `python-dotenv`, `pydantic-settings`
*   **(Future Web Dashboard):** FastAPI/Django + React/Vue

## 7. Database Schema (Key Entities - Refer to `db/models.py`)

*   `PlatformUser`: Users who can create/manage bots on our platform.
*   `ManagedBot`: Represents a Telegram bot. Stores its token, config (e.g., `stars_enabled: Boolean`, `paysupport_text: String`).
*   `SubscriptionPlan`: Defines a subscription offering (name, duration, `price_stars: Integer`, linked resources).
*   `TargetResource`: A Telegram channel or group.
*   `EndUser`: An end-user interacting with a `ManagedBot`.
*   `Subscription`: An active or past subscription. Will store payment details like `payment_gateway: String` ("stars"), `transaction_id: String` (`telegram_payment_charge_id`), `paid_amount_stars: Integer`.
*   `PendingSubscription`: A record for subscription requests (less critical for Stars direct flow but can be used for tracking initiated invoices).
*   `PlanResourceLink`: Association table.

## 8. Current Status (approx. 30% complete) & Refactoring Goals

The current codebase has foundational elements but requires significant refactoring, especially to cleanly integrate diverse payment flows like Telegram Stars.

**Refactoring Goals (including Stars):**

1.  **Solidify Multi-Bot Architecture:** (As before)
2.  **Cleanly Implement Payment Flows:**
    *   Integrate Telegram Stars payment flow (invoice, pre-checkout, successful payment).
    *   Ensure "Payment Sockets" are well-defined interfaces for Stars and future gateways.
3.  **Modular Design:** (As before)
4.  **Robust State Management (FSM):** (As before)
5.  **Scalable Background Tasks:** (As before)
6.  **Complete Core CRUD Functionality:** For plans (with Stars pricing), resources, bot settings (Stars enabling, `/paysupport` text).
7.  **Improve User Experience:** (As before)
8.  **Comprehensive Error Handling and Logging.**
9.  **Prepare for Additional Payment Integrations:** The refactored code for Stars should make it easier to add other gateways (like CryptoBot) by following similar patterns for the "Payment Sockets."

## 9. Project Setup (Current)

1.  Clone the repository.
2.  Create a virtual environment: `python -m venv venv && source venv/bin/activate`
3.  Install dependencies: `pip install -r requirements.txt` (ensure `aiogram>=3.7.0`).
4.  Create a `.env` file based on `.env.example` or the specification.
5.  Initialize the database.
6.  Run the main application: `python main.py`

## 10. Key Challenges to Address in Refactor (including Stars)

*   **Securely Managing Bot Tokens:** (As before)
*   **Telegram API Rate Limits:** (As before)
*   **Atomicity and Reliability:** Ensuring subscription granting/revoking is reliable, especially after Stars `SuccessfulPayment`.
*   **User Experience for Bot Creators:** Making Stars configuration and pricing intuitive.
*   **Payload Management for Stars Invoices:** Ensuring the `invoice_payload` is correctly generated and parsed to link payments to users, plans, and bots.
*   **Contextual Handling of Payment Events:** `BotContextMiddleware` must correctly provide the `ManagedBot` context (DB model and `aiogram.Bot` instance) to `PreCheckoutQuery` and `SuccessfulPayment` handlers.

---

This updated README now reflects the plan to integrate Telegram Stars as a primary payment method.
```
