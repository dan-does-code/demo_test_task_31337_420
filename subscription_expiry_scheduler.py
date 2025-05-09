#!/usr/bin/env python
"""
Scheduler for processing expired subscriptions

This script sets up a scheduler to periodically run the ExpiryProcessor
to handle expired subscriptions. It can be run as a standalone script
or as a service.
"""

import sys
import os
import logging
import asyncio
from datetime import datetime

# Add the parent directory to the path so we can import the app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from app.models.base import SessionLocal
from app.services.expiry_processor import ExpiryProcessor
from app.utils.logger import get_logger

# Configure logging
logger = get_logger("subscription_expiry_scheduler")


async def process_expired_subscriptions_job():
    """Job to process expired subscriptions"""
    logger.info(f"Starting expired subscriptions processing job at {datetime.now()}")
    
    # Create a new database session
    db = SessionLocal()
    try:
        # Process expired subscriptions
        result = await ExpiryProcessor.process_expired_subscriptions(db)
        
        # Log the results
        logger.info(f"Expired subscriptions processing completed: {result}")
        if result.get("processed", 0) > 0:
            logger.info(f"Processed {result['processed']} expired subscriptions")
        if result.get("failed", 0) > 0:
            logger.warning(f"Failed to process {result['failed']} expired subscriptions")
            
    except Exception as e:
        logger.exception(f"Error processing expired subscriptions: {str(e)}")
    finally:
        # Always close the database session
        db.close()


async def main():
    """Main function to set up and run the scheduler"""
    # Create a scheduler
    scheduler = AsyncIOScheduler()
    
    # Add job to run every day at 00:00
    # This can be customized based on requirements
    scheduler.add_job(
        process_expired_subscriptions_job,
        CronTrigger(hour=0, minute=0),  # Run at midnight every day
        id="process_expired_subscriptions",
        name="Process Expired Subscriptions",
        replace_existing=True,
    )
    
    # For testing purposes, you can also add a job that runs more frequently
    # Uncomment the following lines to run the job every minute for testing
    # scheduler.add_job(
    #     process_expired_subscriptions_job,
    #     'interval',
    #     minutes=1,
    #     id="test_process_expired_subscriptions",
    #     name="Test Process Expired Subscriptions",
    # )
    
    # Start the scheduler
    scheduler.start()
    logger.info("Scheduler started. Press Ctrl+C to exit.")
    
    # Keep the script running
    try:
        # Run forever
        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        # Shutdown the scheduler gracefully
        logger.info("Shutting down scheduler...")
        scheduler.shutdown()
        logger.info("Scheduler shut down successfully.")


if __name__ == "__main__":
    # Run the main function
    asyncio.run(main())