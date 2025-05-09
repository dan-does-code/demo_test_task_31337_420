# Webhook Registration Process

## Overview

This document describes the process for registering webhooks with Telegram for managed bots. The system now uses a secure webhook secret for routing instead of partial bot tokens, which enhances security by not exposing any part of the bot token in URLs.

## Webhook Secret

Each managed bot has a unique `webhook_secret` that is used for webhook routing. This secret is:

- Automatically generated when a new bot is created
- Unique for each bot
- Used in the webhook URL path parameter

## Registration Process

### For New Bots

When a new bot is created through the API:

1. A webhook secret is automatically generated and stored in the database
2. The webhook URL should be set with Telegram using the following format:
   ```
   https://your-domain.com/webhook/{webhook_secret}
   ```

### For Existing Bots

For bots that existed before this feature was implemented:

1. Run the `scripts/generate_webhook_secrets.py` script to generate webhook secrets for all existing bots
2. The script will output the webhook URL for each bot
3. Update the webhook URL with Telegram for each bot

## Setting the Webhook with Telegram

To set the webhook URL with Telegram, use the Telegram Bot API's `setWebhook` method:

```
https://api.telegram.org/bot{bot_token}/setWebhook?url=https://your-domain.com/webhook/{webhook_secret}
```

Replace:
- `{bot_token}` with your bot's token
- `your-domain.com` with your actual domain
- `{webhook_secret}` with the bot's webhook secret

## Retrieving a Bot's Webhook Secret

You can retrieve a bot's webhook secret through the API or directly from the database. The webhook secret is included in the `ManagedBotResponse` schema when retrieving bot information.

## Security Considerations

- The webhook secret should be treated as sensitive information
- Do not share the webhook secret publicly
- If a webhook secret is compromised, it can be regenerated through the API