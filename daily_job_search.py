#!/usr/bin/env python3
"""
Daily job search automation script
Run this via cron job or Railway cron trigger
"""

import os
import sys
import logging
from datetime import datetime
from job_search_agent import main as run_job_search

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('job_search.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

def daily_search():
    """Run daily job search and log results"""
    try:
        logging.info("Starting daily job search...")
        
        # Run the job search
        run_job_search()
        
        logging.info("Daily job search completed successfully")
        
    except Exception as e:
        logging.error(f"Daily job search failed: {str(e)}")
        # You could add notification here (email, Slack, etc.)
        raise

if __name__ == "__main__":
    daily_search()